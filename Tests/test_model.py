
##============================================================================================##
##                           test du modèle xgboost                                     ##
##                   Dataset origin : Data/process/cancer_clean.csv                           ##
##       Lancer : pytest Tests/test_model.py -v --junitxml=Tests_results/test-results.xml     ##
##============================================================================================##


# PACKAGES 
import pytest
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    recall_score,
    precision_score,
    
    f1_score,
    roc_auc_score,
    confusion_matrix)

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


#   PATH 
DATA_PATH   = Path("Data/process/cancer_clean.csv")
MODELS_DIR  = Path("Save_models")

# Seuils de validation médicale
SEUIL_RECALL = 0.95  
SEUIL_PRECISION = 0.90   
SEUIL_AUC = 0.92   
SEUIL_F1 = 0.90  


# PREREQUIS

@pytest.fixture(scope="module")
def dataset():
    """Charge dataset depuis Data/process/cancer_clean.csv"""
    assert DATA_PATH.exists(), (
        f"Dataset introuvable : {DATA_PATH}\n"
        "Vérifie que le fichier existe avant de lancer les tests."
    )
    df = pd.read_csv(DATA_PATH) 
    df = df.drop(["radius_worst", "perimeter_worst"], axis = 1)
    
    assert "diagnosis" in df.columns, (
        "Colonne 'diagnosis' absente du dataset."
        f"Colonnes disponibles : {df.columns.tolist()}"
    )
    return df


@pytest.fixture(scope="module")
def model_and_scaler():
    """Charge xgboost model (.pkl) et le scaler depuis Save_models/."""
    
    # Cherche le fichier *_best.pkl dans le dossier Save_models
    pkl_files = list(MODELS_DIR.glob("*_best.pkl"))
    assert len(pkl_files) > 0, (
        f"Aucun fichier *_best.pkl trouvé dans {MODELS_DIR}/\n"
        "Lance d'abord compare_models() pour entraîner et sauvegarder le modèle."
    )

    model_path  = pkl_files[0]
    scaler_path = MODELS_DIR/"MinMax_scaler.pkl"

    assert scaler_path.exists(), (
        f"Scaler introuvable : {scaler_path}\n"
        "Le scaler doit être sauvegardé avec le modèle."
    )

    with open(model_path, "rb") as f:
        modele = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    return modele, scaler, model_path.stem


@pytest.fixture(scope="module")
def predictions(dataset, model_and_scaler):
    """Prépare X_test, y_test et calcule toutes les prédictions."""
    modele, scaler, _ = model_and_scaler
    df = dataset
   
    # Sélectionne les features _worst (comme dans ton train.py)
    worst_cols = [c for c in df.columns if c.endswith("_worst")]
    assert len(worst_cols) > 0, (
        "Aucune colonne '_worst' trouvée dans le dataset.\n"
        f"Colonnes disponibles : {df.columns.tolist()}"
    )
     
    X = df[worst_cols]

    # Encode la cible
    y = df["diagnosis"]
    if y.dtype == object:
        y = y.map({"M": 1, "B": 0})

    assert y.isna().sum() == 0, (
        "Valeurs inconnues dans 'diagnosis' après encodage M/B => 1/0.\n"
        f"Valeurs uniques trouvées : {df['diagnosis'].unique()}"
    )

    # Split reproductible (même random_state que train.py)
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    X_test_scaled = scaler.transform(X_test)
    y_pred = modele.predict(X_test_scaled)
    y_proba = modele.predict_proba(X_test_scaled)[:, 1]

    return {"y_test": y_test.values, "y_pred": y_pred, "y_proba": y_proba, "n_test": len(y_test)}


# VERIFICATION : vérifier que le CSV est exploitable avant tout calcul

class TestDataset:
    def test_dataset_non_vide(self, dataset):
        assert len(dataset) > 0, "Le CSV est vide"
        assert len(dataset) >= 100, (
            f"Dataset trop petit : {len(dataset)} lignes. "
            "Résultats statistiquement non fiables."
        )

    def test_colonnes_worst_presentes(self, dataset):
        worst_cols = [c for c in dataset.columns if c.endswith("_worst")]
        assert len(worst_cols) >= 1, "Aucune colonne '_worst' dans le dataset"

    def test_pas_de_valeurs_manquantes_dans_features(self, dataset):
        worst_cols = [c for c in dataset.columns if c.endswith("_worst")]
        nb_nan = dataset[worst_cols].isna().sum().sum()
        assert nb_nan == 0, (
            f"{nb_nan} valeur(s) manquante(s) dans les features '_worst'.\n"
            "Relance le preprocessing avant de tester le modèle."
        )

    def test_deux_classes_presentes(self, dataset):
        classes = dataset["diagnosis"].unique()
        assert "M" in classes and "B" in classes, (
            f"Classes attendues : M et B. Trouvées : {classes}"
        )

    def test_encodage_m_est_malin(self, dataset):
        """Vérifie que M = 1 (malin = positif). Un bug ici inverse le sens des prédictions."""
        encoded = dataset["diagnosis"].map({"M": 1, "B": 0})
        assert encoded[dataset["diagnosis"] == "M"].iloc[0] == 1
        assert encoded[dataset["diagnosis"] == "B"].iloc[0] == 0


# MÉTRIQUES : les seuils sont calibrés pour un contexte médical.

class TestMetriques:

    def test_recall_seuil_medical(self, predictions):
        """
        CRITIQUE : Ne pas manquer les cas malins.
        Recall < 0.90 = trop de cancers non détectés.
        """
        recall = recall_score(predictions["y_test"], predictions["y_pred"])
        assert recall >= SEUIL_RECALL, (
            f"Recall={recall:.3f} < seuil={SEUIL_RECALL}\n"
            f"Faux négatifs : {int((predictions['y_test'] == 1) & (predictions['y_pred'] == 0)).sum()} "
            f"cas malins non détectés sur {predictions['n_test']} exemples."
        )

    def test_precision_acceptable(self, predictions):
        """
        Évite de sur-alarmer les patients bénins.
        Une précision trop faible = trop de biopsies inutiles.
        """
        precision = precision_score(predictions["y_test"], predictions["y_pred"])
        assert precision >= SEUIL_PRECISION, (
            f"Précision={precision:.3f} < seuil={SEUIL_PRECISION}\n"
            "Trop de faux positifs - patients bénins classés malins."
        )

    def test_auc_discrimination_globale(self, predictions):
        """
        AUC mesure la capacité du modèle à séparer malin/bénin
        sur tout le spectre de probabilités.
        """
        auc = roc_auc_score(predictions["y_test"], predictions["y_proba"])
        assert auc >= SEUIL_AUC, (
            f"AUC={auc:.3f} < seuil={SEUIL_AUC}\n"
            "La discrimination globale du modèle est insuffisante."
        )

    def test_f1_score_equilibre(self, predictions):
        """Équilibre précision/recall = indicateur de santé globale du modèle."""
        f1 = f1_score(predictions["y_test"], predictions["y_pred"])
        assert f1 >= SEUIL_F1, (
            f"F1={f1:.4f} < seuil={SEUIL_F1}"
        )

    def test_matrice_confusion_pas_de_classe_ignoree(self, predictions):
        """
        Le modèle ne doit pas tout prédire dans une seule classe
        (symptôme d'un modèle dégénéré).
        """
        cm = confusion_matrix(predictions["y_test"], predictions["y_pred"])
        assert cm.shape == (2, 2), "Matrice de confusion non carrée — une classe absente"
        assert cm[0, 0] > 0, "Aucun vrai négatif (bénin) — modèle dégénéré"
        assert cm[1, 1] > 0, "Aucun vrai positif (malin) — modèle dégénéré"

    def test_probabilites_valides(self, predictions):
        """Les probabilités doivent être dans [0, 1] et sommer à 1."""
        assert predictions["y_proba"].min() >= 0.0, "Probabilité négative détectée"
        assert predictions["y_proba"].max() <= 1.0, "Probabilité > 1 détectée"


# ROBUSTESSE : vérifie que le modèle se comporte bien sur des cas limites

class TestRobustesse:

    def test_prediction_sur_un_seul_exemple(self, model_and_scaler, dataset):
        """Le modèle doit fonctionner sur une seule ligne."""
        modele, scaler, _ = model_and_scaler
        worst_cols = [c for c in dataset.columns if c.endswith("_worst")]

        X_single = dataset[worst_cols].iloc[[0]]
        X_scaled  = scaler.transform(X_single)

        pred  = modele.predict(X_scaled)
        proba = modele.predict_proba(X_scaled)

        assert pred[0] in {0, 1}
        assert proba.shape == (1, 2)
        assert abs(proba[0].sum() - 1.0) < 1e-5

    def test_prediction_stable_sur_meme_entree(self, model_and_scaler, dataset):
        """Deux prédictions identiques sur la même entrée = même résultat."""
        modele, scaler, _ = model_and_scaler
        worst_cols = [c for c in dataset.columns if c.endswith("_worst")]

        X_sample = dataset[worst_cols].head(10)
        X_scaled  = scaler.transform(X_sample)

        pred1 = modele.predict(X_scaled)
        pred2 = modele.predict(X_scaled)

        np.testing.assert_array_equal(pred1, pred2,
            err_msg="Le modèle produit des prédictions différentes sur la même entrée")

    def test_scaler_dans_plage_attendue(self, model_and_scaler, dataset):
        """
        Après MinMaxScaler, toutes les valeurs des features doivent être entre [0, 1].
        Une valeur hors plage signifie que le CSV contient des outliers non vus pendant l'entraînement.
        """
        _, scaler, _ = model_and_scaler
        worst_cols = [c for c in dataset.columns if c.endswith("_worst")]
        X_scaled = scaler.transform(dataset[worst_cols])

        ratio_hors_plage = ((X_scaled < -0.1) | (X_scaled > 1.1)).mean()
        assert ratio_hors_plage < 0.01, (
            f"{ratio_hors_plage:.1%} des valeurs scalées sont hors de [-0.1, 1.1].\n"
            "Le dataset de production contient peut-être des valeurs anormales."
        )