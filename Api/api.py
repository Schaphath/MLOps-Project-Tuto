from contextlib import asynccontextmanager
import logging
from pathlib import Path
import pickle
from typing import Literal

from fastapi import FastAPI, HTTPException, status
import numpy as np
from pydantic import BaseModel, Field

# Configuration minimale du Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Chemins des artefacts
MODEL_PATH = Path("save_models/xgboost_best.pkl")
SCALER_PATH = Path("save_models/MinMax_scaler.pkl")

# Ordre strict des features attendu par le modèle
FEATURE_ORDER = [
    "texture_worst", "area_worst", "smoothness_worst", "compactness_worst",
    "concavity_worst", "concave_points_worst", "symmetry_worst", "fractal_dimension_worst"
]

# Conteneur global pour les modèles
class MLArtifacts:
    model = None
    scaler = None

# Gestion du cycle de vie (Lifespan) : Chargement unique des modèles au démarrage
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Chargement des artefacts de Machine Learning...")
    try:
        with open(MODEL_PATH, "rb") as f:
            MLArtifacts.model = pickle.load(f)
            
        with open(SCALER_PATH, "rb") as f:
            MLArtifacts.scaler = pickle.load(f)
            
        logger.info("Modèle et Scaler chargés avec succès.")
    except Exception as e:
        logger.critical(f"Impossible de charger les modèles : {e}")
        raise RuntimeError(e)
    yield
    # Libération des ressources à l'arrêt
    MLArtifacts.model = None
    MLArtifacts.scaler = None

# Initialisation de l'application
app = FastAPI(title="OncoScan AI - API", version="1.0.0", lifespan=lifespan)

# Validation stricte des données entrantes (Pydantic)
class PredictionInput(BaseModel):
    texture_worst: float = Field(..., gt=0)
    area_worst: float = Field(..., gt=0)
    smoothness_worst: float = Field(..., gt=0)
    compactness_worst: float = Field(..., ge=0)
    concavity_worst: float = Field(..., ge=0)
    concave_points_worst: float = Field(..., ge=0)
    symmetry_worst: float = Field(..., gt=0)
    fractal_dimension_worst: float = Field(..., gt=0)

class PredictionOutput(BaseModel):
    prediction: Literal["M", "B"]
    probability_malignant: float

# Endpoint de vérification de l'état (Healthcheck pour Docker)
@app.get("/health", status_code=status.HTTP_200_OK)

def health_check():
    if MLArtifacts.model is None or MLArtifacts.scaler is None:
        raise HTTPException(status_code=503, detail="Modèles non chargés")
    return {"status": "healthy"}

# Endpoint principal d'inférence
@app.post("/predict", response_model=PredictionOutput, status_code=status.HTTP_200_OK)

def predict(data: PredictionInput):
    try:
        # 1. Extraction et alignement des features selon l'ordre strict
        input_dict = data.model_dump()
        features = np.array([[input_dict[f] for f in FEATURE_ORDER]])
        
        # 2. Transformation et Inférence
        features_scaled = MLArtifacts.scaler.transform(features)
        pred_raw = int(MLArtifacts.model.predict(features_scaled)[0])
        prob_malignant = float(MLArtifacts.model.predict_proba(features_scaled)[0][1])
        
        return PredictionOutput(
            prediction="M" if pred_raw == 1 else "B",
            probability_malignant=round(prob_malignant, 4)
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'inférence : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur interne est survenue lors du calcul de la prédiction."
        )
        

# Run api : uvicorn api:app --reload 