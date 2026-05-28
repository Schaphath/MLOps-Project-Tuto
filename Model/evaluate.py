#========================#
#   evaluate.py          #
#   Evaluation modèle    #
#========================#
import sys
import json
import pickle
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from sklearn.metrics import (
    recall_score,
    precision_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
)


# Seuil (en dessous de se seuil, ALERTE !!!!!)
SEUIL_RECALL = 0.90 


# Fonction d'évaluation 
def evaluate(data_path = "Data/evaluate/cancer_eval.csv", models_dir = "Save_models",
             output_dir = "Save_models", save_fig = True):
    """
    Evalue le modele sauvegardé sur de nouvelles données.

    Retourne : 
    
    - metrics : dict {"recall", "precision", "f1", "auc", "passed"};
    - fig_cm  : Figure Matrice de confusion.
    
    """

    # Chargement des donnees 
    df = pd.read_csv(data_path, sep=",")
    df = df.drop(["radius_worst", "perimeter_worst"], axis = 1)
    
    
    worst_cols   = [c for c in df.columns if c.endswith("_worst")]
    feature_cols = worst_cols 
    
    X = df[feature_cols]
    y = df["diagnosis"].map({"M": 1, "B": 0})

    print(f"Donnees chargées : {len(df)} lignes | {len(feature_cols)} features")
    print(f"  Benin (0) : {(y==0).sum()}  |  Malin (1) : {(y==1).sum()}")


    # Chargement du modèle et du scaler 
    models_path = Path(models_dir)
    pkl_files   = list(models_path.glob("*_best.pkl"))
    
    assert len(pkl_files) > 0, f"Aucun *_best.pkl dans {models_dir}/"

    with open(pkl_files[0], "rb") as f: model  = pickle.load(f)
    with open(models_path/"MinMax_scaler.pkl", "rb") as f: scaler = pickle.load(f)

    model_name = pkl_files[0].stem.replace("_best", "").replace("_", " ").title()
    print(f"Modèle chargé : {model_name}")

    # Prédiction 
    X_scaled = scaler.transform(X)
    y_pred   = model.predict(X_scaled)
    y_proba  = model.predict_proba(X_scaled)[:, 1]

    # Métriques 
    recall    = recall_score(y, y_pred)
    precision = precision_score(y, y_pred)
    f1 = f1_score(y, y_pred)
    auc = roc_auc_score(y, y_proba)
    passed = recall >= SEUIL_RECALL

    metrics = {
        "model": model_name,
        "n_samples": int(len(y)),
        "recall": round(float(recall),4),
        "precision": round(float(precision), 4),
        "f1": round(float(f1),4),
        "auc": round(float(auc),4),
        "threshold": SEUIL_RECALL,
        "passed": bool(passed),
    }

    # Affichage console (visible dans les logs Jenkins par exemple) 
    cm = confusion_matrix(y, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print(f"\n{'='*50}")
    print(f"METRIQUES — {model_name}")
    print(f"{'='*50}")
    print(f"Recall : {recall:.4f}  (seuil >= {SEUIL_RECALL})")
    print(f"Precision : {precision:.4f}")
    print(f"F1-score : {f1:.4f}")
    print(f"AUC : {auc:.4f}")
    print(f"{'='*50}")
    print(f"TN={tn}  FP={fp}")
    print(f"FN={fn}  TP={tp} (FN = malins manqués)")
    print(f"{'='*50}")

    status = "PASSED -- déploiement autorisé" if passed else "FAILED -- déploiement bloqué"
    
    print(f"Verdict : {status}")
    print(f"{'='*50}\n")

    # Sauvegarder les métrics dans metrics.json 
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    metrics_file = out_path / "metrics.json"
    
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"metrics.json sauvegarde : {metrics_file}")

    # Matrice de confusion 
    fig_cm, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig_cm.suptitle(f"Matrice de Confusion — {model_name}", 
                    fontsize=13, fontweight="bold", y=1.02)


    # Matrice de confusion avec valeurs absolues
    ConfusionMatrixDisplay(cm, display_labels=["Benin (0)", "Malin (1)"]).plot(
        ax=axes[0], colorbar=False, cmap="Blues")
    
    axes[0].set_title("Valeurs absolues",  fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Classe predite",   fontsize=10)
    axes[0].set_ylabel("Classe reelle",    fontsize=10)
    
    for t in axes[0].texts: t.set_fontsize(16); t.set_fontweight("bold")

    # Matrice de confusion avec pourcentages par classe 
    cm_norm = confusion_matrix(y, y_pred, normalize="true")
    
    ConfusionMatrixDisplay(cm_norm, display_labels=["Benin (0)", "Malin (1)"]).plot(
        ax=axes[1], colorbar=False, cmap="Greens")
    
    axes[1].set_title("Normalisee — % par classe reelle", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Classe predite", fontsize=10)
    axes[1].set_ylabel("Classe reelle",  fontsize=10)
   
    for t in axes[1].texts:
        t.set_text(f"{float(t.get_text())*100:.1f}%")
        t.set_fontsize(16); t.set_fontweight("bold")

    legend_elems = [
        mpatches.Patch(color="#d0e8ff", label=f"TN={tn}  Benins bien classes"),
        mpatches.Patch(color="#fdd49e", label=f"FP={fp}  Benins -> fausse alarme"),
        mpatches.Patch(color="#d7191c", label=f"FN={fn}  Malins manques  !!!"),
        mpatches.Patch(color="#2b83ba", label=f"TP={tp}  Malins bien detectes"),
    ]
    
    fig_cm.legend(handles=legend_elems, loc="lower center", ncol=2,
                  fontsize=10, bbox_to_anchor=(0.5, -0.12), frameon=True)
    
    plt.tight_layout()

    if save_fig:
        fig_path = out_path / "confusion_matrix.png"
        fig_cm.savefig(fig_path, dpi=150, bbox_inches="tight")
        print(f"Figure sauvegardee  : {fig_path}")

    return metrics, fig_cm


# Entrypoint 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation du modèle cancer du sein")
    parser.add_argument("--data", default="Data/evaluate/cancer_eval.csv")
    parser.add_argument("--models_dir", default="Save_models")
    parser.add_argument("--output_dir", default="Save_models")
    parser.add_argument("--no_fig", action="store_true")
    args = parser.parse_args()

    metrics, _ = evaluate(
        data_path  = args.data,
        models_dir = args.models_dir,
        output_dir = args.output_dir,
        save_fig   = not args.no_fig,
    )

    # Exit code 1 si le recall est insuffisant 
    if not metrics["passed"]:
        print(f"ECHEC : Recall={metrics['recall']} < seuil={metrics['threshold']}")
        sys.exit(1)

    print("Validation reussie. Deploiement autorise.")
    sys.exit(0)
    
    
    
    
    
    
"""
# Conclusion : 

# Modèle près pour la production. 
# Mais attention, en raison du nombre de ligne reduit dans notre dataset. Il serait judicieux de faire attention à ces métriques. 
# Il se pourrait que le modèle est pu voir les mêmes données plusieurs fois. 
# Il faudra collerder d'avantage de données et tester réellement les performance de ce modèle et temps réel. 
# our une approche pédagogique la démarche reste correcte.

""" 
