# packages
import os
import time
import pickle
import logging
from pathlib import Path
from typing import Literal, Optional
from contextlib import asynccontextmanager

import numpy as np
import psycopg2
from psycopg2 import pool
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status


# CONFIGURATION DU LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# CONFIGURATION
MODEL_PATH = Path("save_models/xgboost_best.pkl")
SCALER_PATH = Path("save_models/MinMax_scaler.pkl")

FEATURE_ORDER = [
    "texture_worst",
    "area_worst",
    "smoothness_worst",
    "compactness_worst",
    "concavity_worst",
    "concave_points_worst",
    "symmetry_worst",
    "fractal_dimension_worst"
]

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "oncoscan_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "postgres")


# GESTIONNAIRE DES ARTEFACTS ET DE LA BASE DE DONNÉES
class AppState:
    """Gestionnaire d'état pour les artefacts ML et le pool SQL."""
    model = None
    scaler = None
    db_pool: Optional[pool.ThreadedConnectionPool] = None


def init_db_pool(retries: int = 5, delay: int = 3) -> Optional[pool.ThreadedConnectionPool]:
    """Initialise un pool de connexions PostgreSQL résilient avec retries."""
    for i in range(retries):
        try:
            db_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            logger.info("Pool de connexions PostgreSQL initialisé avec succès.")
            return db_pool
        except psycopg2.OperationalError as e:
            if i < retries - 1:
                logger.warning(
                    f"Base de données inaccessible ({e}). "
                    f"Nouvelle tentative dans {delay}s... ({i + 1}/{retries})"
                )
                time.sleep(delay)
            else:
                logger.critical(
                    "Impossible d'initialiser le pool PostgreSQL après plusieurs tentatives."
                )
                return None
    return None


# CYCLE DE VIE DE L'APPLICATION (LIFESPAN)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Chargement des artefacts du modèle
    logger.info("Chargement des artefacts ...")
    try:
        with open(MODEL_PATH, "rb") as f:
            AppState.model = pickle.load(f)

        with open(SCALER_PATH, "rb") as f:
            AppState.scaler = pickle.load(f)

        logger.info("Modèle et Scaler chargés avec succès.")
    except Exception as e:
        logger.critical(f"Erreur critique lors du chargement des modèles : {e}")
        raise RuntimeError(f"Impossible de charger les artefacts : {e}")

    # 2. Initialisation du Pool PostgreSQL
    AppState.db_pool = init_db_pool()

    yield

    # 3. Libération des ressources à la fermeture
    if AppState.db_pool:
        AppState.db_pool.closeall()
        logger.info("Toutes les connexions du pool PostgreSQL ont été fermées.")
    AppState.model = None
    AppState.scaler = None


# Initialisation FastAPI
app = FastAPI(
    title="OncoScan AI - API",
    description="API pour la prédiction de malignité tumorale.",
    version="1.2.0",
    lifespan=lifespan
)


# SCHÉMAS DE VALIDATION (PYDANTIC)
class PredictionInput(BaseModel):
    texture_worst: float = Field(..., gt=0, description="Valeur extrême de la texture cellulaire")
    area_worst: float = Field(..., gt=0, description="Valeur extrême de la surface cellulaire")
    smoothness_worst: float = Field(..., gt=0, description="Valeur extrême du lissé cellulaire")
    compactness_worst: float = Field(..., ge=0, description="Valeur extrême de la compacité")
    concavity_worst: float = Field(..., ge=0, description="Valeur extrême de la concavité")
    concave_points_worst: float = Field(..., ge=0, description="Valeur extrême des points concaves")
    symmetry_worst: float = Field(..., gt=0, description="Valeur extrême de la symétrie")
    fractal_dimension_worst: float = Field(..., gt=0, description="Valeur extrême de la dimension fractale")


class PredictionOutput(BaseModel):
    prediction: Literal["M", "B"]
    probability_malignant: float


# ENDPOINTS
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Vérification de l'état de santé de l'API et de la dépendance BDD."""
    models_ready = AppState.model is not None and AppState.scaler is not None
    db_ready = AppState.db_pool is not None and not AppState.db_pool.closed

    if not models_ready:
        raise HTTPException(status_code=503, detail="Modèles prédictifs non chargés en mémoire.")

    return {
        "status": "healthy",
        "database_connected": db_ready
    }


@app.post("/predict", response_model=PredictionOutput, status_code=status.HTTP_200_OK)
def predict(data: PredictionInput):
    """Calcule l'inférence XGBoost et log la transaction de manière anonyme en BDD."""
    if AppState.model is None or AppState.scaler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service d'inférence est temporairement indisponible."
        )

    try:
        # 1. Alignement des caractéristiques et Inférence
        input_dict = data.model_dump()
        features = np.array([[input_dict[f] for f in FEATURE_ORDER]])

        features_scaled = AppState.scaler.transform(features)
        pred_raw = int(AppState.model.predict(features_scaled)[0])
        prob_malignant = float(AppState.model.predict_proba(features_scaled)[0][1])

        prediction_label = "M" if pred_raw == 1 else "B"
        probability_pct = round(prob_malignant * 100, 2)

        # 2. Persistance via le Pool Thread-Safe
        if AppState.db_pool:
            conn = None
            try:
                conn = AppState.db_pool.getconn()
                with conn.cursor() as cursor:
                    query = """
                        INSERT INTO predictions (
                            texture_worst, area_worst, smoothness_worst, compactness_worst,
                            concavity_worst, concave_points_worst, symmetry_worst,
                            fractal_dimension_worst, prediction, probability_pct
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """
                    cursor.execute(
                        query,
                        (input_dict["texture_worst"],
                         input_dict["area_worst"],
                         input_dict["smoothness_worst"],
                         input_dict["compactness_worst"],
                         input_dict["concavity_worst"],
                         input_dict["concave_points_worst"],
                         input_dict["symmetry_worst"],
                         input_dict["fractal_dimension_worst"],
                         prediction_label,
                         probability_pct)
                    )
                    conn.commit()
            except Exception as db_err:
                if conn:
                    conn.rollback()
                logger.error(f"Erreur d'écriture BDD (Transaction annulée) : {db_err}")
            finally:
                if conn:
                    AppState.db_pool.putconn(conn)
        else:
            logger.warning("Sauvegarde impossible : Le pool de la base de données est inactif.")

        return PredictionOutput(
            prediction=prediction_label,
            probability_malignant=round(prob_malignant, 3)
        )

    except Exception as e:
        logger.error(f"Erreur interne lors du traitement : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne est survenue lors du calcul de la prédiction."
        )
