import os
import requests
import streamlit as st


# CONFIGURATION DE LA PAGE STREAMLIT
st.set_page_config(
    page_title="OncoScan AI",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Api url
API_URL = os.getenv("API_URL", "http://api:8000/predict")


# CONFIGURATION ET CHARGEMENT DU CLIENT HTTP PERSISTANT
@st.cache_resource
def get_http_session() -> requests.Session:
    """Instancie une session HTTP réutilisable (Connexion HTTP Keep-Alive)."""
    session = requests.Session()
    return session


http_client = get_http_session()


# MÉTADONNÉES
FEATURES_META = {
    "texture_worst": {
        "label": "texture_worst",
        "min": 10.0, "max": 50.0, "default": 25.41,
        "format": "%.2f",
    },
    "area_worst": {
        "label": "area_worst",
        "min": 100.0, "max": 4500.0, "default": 880.58,
        "format": "%.2f",
    },
    "smoothness_worst": {
        "label": "smoothness_worst",
        "min": 0.05, "max": 0.25, "default": 0.1324,
        "format": "%.4f",
    },
    "compactness_worst": {
        "label": "compactness_worst",
        "min": 0.02, "max": 1.20, "default": 0.2542,
        "format": "%.4f",
    },
    "concavity_worst": {
        "label": "concavity_worst",
        "min": 0.0, "max": 1.30, "default": 0.2722,
        "format": "%.4f",
    },
    "concave_points_worst": {
        "label": "concave_points_worst",
        "min": 0.0, "max": 0.30, "default": 0.1146,
        "format": "%.4f",
    },
    "symmetry_worst": {
        "label": "symmetry_worst",
        "min": 0.10, "max": 0.70, "default": 0.2901,
        "format": "%.4f",
    },
    "fractal_dimension_worst": {
        "label": "fractal_dimension_worst",
        "min": 0.05, "max": 0.25, "default": 0.0839,
        "format": "%.4f",
    },
}


# INJECTION DES STYLES CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"], .main {
    background-color: #070d1a !important;
    background-image: none !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stHeader"] { background-color: #070d1a !important; border-bottom: none !important; }
[data-testid="stMainBlockContainer"] { padding-top: 2rem !important; padding-bottom: 4rem !important; max-width: 840px !important; }
[data-testid="stForm"] { background: #0d1526 !important; border: 1px solid #1e2d4a !important; border-radius: 20px !important; padding: 1.8rem 2rem !important; box-shadow: 0 8px 40px rgba(0,0,0,0.45) !important; }
[data-testid="stNumberInput"] label, [data-testid="stNumberInput"] label p { color: #a8c0e0 !important; font-size: 0.8rem !important; font-weight: 500 !important; letter-spacing: 0.2px !important; }
[data-testid="stNumberInput"] input { background: #111e35 !important; color: #e8f0ff !important; border: 1.5px solid #1e3255 !important; border-radius: 10px !important; font-size: 0.95rem !important; font-weight: 500 !important; caret-color: #38bdf8 !important; }
[data-testid="stNumberInput"] input:focus { border-color: #3b82f6 !important; box-shadow: 0 0 0 3px rgba(59,130,246,0.18) !important; outline: none !important; }
[data-testid="stNumberInput"] button { background: #1a2d4e !important; color: #a8c0e0 !important; border: 1px solid #1e3255 !important; border-radius: 8px !important; }
[data-testid="stNumberInput"] button:hover { background: #1e3562 !important; color: #38bdf8 !important; }
[data-testid="stTooltipIcon"] svg { color: #3b6fa0 !important; fill: #3b6fa0 !important; }

[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem 2rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.4px !important;
    box-shadow: 0 4px 20px rgba(37,99,235,0.4) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
    box-shadow: 0 6px 28px rgba(37,99,235,0.55) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stCaptionContainer"] p, .stCaption { color: #4a6388 !important; font-size: 0.78rem !important; }
[data-testid="stSpinner"] p { color: #7098c8 !important; }
[data-testid="stExpander"] { background: #0d1526 !important; border: 1px solid #1e2d4a !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary { color: #7098c8 !important; font-size: 0.84rem !important; }
[data-testid="stExpander"] summary:hover { color: #38bdf8 !important; }
hr { border-color: #1a2a42 !important; margin: 1.4rem 0 !important; }

/* COMPOSANTS PERSONNALISÉS (HERO ET BANNER) */
.hero-banner { background: linear-gradient(135deg, #0c1a36 0%, #112248 50%, #0e2650 100%); border: 1px solid #1a3060; border-radius: 20px; padding: 2.2rem 2.6rem 2rem; margin-bottom: 1.6rem; position: relative; overflow: hidden; box-shadow: 0 16px 48px rgba(0,0,0,0.5); }
.hero-banner::before { content: ''; position: absolute; top: -70px; right: -50px; width: 240px; height: 240px; border-radius: 50%; background: radial-gradient(circle, rgba(56,189,248,0.14) 0%, transparent 68%); pointer-events: none; }
.hero-banner::after { content: ''; position: absolute; bottom: -50px; left: -40px; width: 200px; height: 200px; border-radius: 50%; background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 68%); pointer-events: none; }
.hero-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(56,189,248,0.1); border: 1px solid rgba(56,189,248,0.28); color: #38bdf8; font-size: 0.7rem; font-weight: 600; letter-spacing: 1.8px; text-transform: uppercase; padding: 4px 12px; border-radius: 99px; margin-bottom: 0.8rem; }
.hero-title { font-family: 'DM Serif Display', serif; font-size: 2.3rem; color: #eaf2ff; margin: 0 0 0.5rem; letter-spacing: -0.5px; line-height: 1.15; }
.hero-title span { font-style: italic; color: #38bdf8; }
.hero-subtitle { font-size: 0.9rem; color: #7098c8; margin: 0; font-weight: 300; line-height: 1.65; max-width: 580px; }
.form-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1.4rem; padding-bottom: 1rem; border-bottom: 1px solid #1a2a42; }
.form-header-dot { width: 8px; height: 8px; border-radius: 50%; background: #3b82f6; box-shadow: 0 0 8px rgba(59,130,246,0.7); flex-shrink: 0; }
.form-header-text { font-size: 0.72rem; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: #4a6fa5; margin: 0; }

/* CARTES DE RÉSULTATS INFÉRENCE */
.result-card { border-radius: 18px; padding: 1.8rem 2rem; margin-top: 0.6rem; border: 1px solid; position: relative; overflow: hidden; }
.result-card::before { content: ''; position: absolute; top: 0; right: 0; width: 160px; height: 160px; border-radius: 50%; opacity: 0.08; transform: translate(40px, -40px); }
.result-malignant { background: linear-gradient(135deg, #1a0a0a 0%, #2d0f0f 100%); border-color: #7f1d1d; }
.result-malignant::before { background: #ef4444; }
.result-benign { background: linear-gradient(135deg, #071a0e 0%, #0d2b18 100%); border-color: #14532d; }
.result-benign::before { background: #22c55e; }
.result-label { font-size: 0.72rem; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 0.4rem; }
.result-malignant .result-label { color: #f87171; }
.result-benign .result-label { color: #4ade80; }
.result-title { font-family: 'DM Serif Display', serif; font-size: 1.5rem; margin: 0 0 1rem; line-height: 1.2; }
.result-malignant .result-title { color: #fca5a5; }
.result-benign .result-title { color: #86efac; }
.result-prob-row { display: flex; align-items: baseline; gap: 8px; margin-bottom: 0.8rem; }
.result-prob { font-size: 3rem; font-weight: 700; line-height: 1; }
.result-malignant .result-prob { color: #f87171; }
.result-benign .result-prob { color: #4ade80; }
.result-prob-label { font-size: 0.82rem; font-weight: 400; }
.result-malignant .result-prob-label { color: #9b5a5a; }
.result-benign .result-prob-label { color: #4a8a62; }
.prob-bar-wrap { background: rgba(255,255,255,0.07); border-radius: 99px; height: 8px; margin: 0.6rem 0 1.2rem; overflow: hidden; }
.prob-bar-fill { height: 100%; border-radius: 99px; }
.prob-bar-malignant { background: linear-gradient(90deg, #ef4444, #f87171); }
.prob-bar-benign { background: linear-gradient(90deg, #22c55e, #4ade80); }
.reco-box { border-radius: 12px; padding: 0.9rem 1.1rem; font-size: 0.84rem; line-height: 1.65; border: 1px solid; }
.result-malignant .reco-box { background: rgba(239,68,68,0.07); border-color: rgba(239,68,68,0.2); color: #e2a0a0; }
.result-benign .reco-box { background: rgba(34,197,94,0.07); border-color: rgba(34,197,94,0.2); color: #86c8a0; }
.reco-box strong { font-weight: 600; }
.result-malignant .reco-box strong { color: #fca5a5; }
.result-benign .reco-box strong { color: #a7f3c4; }
.app-footer { text-align: center; color: #2a3d5a; font-size: 0.73rem; margin-top: 2.5rem; padding-top: 1.2rem; border-top: 1px solid #111e35; line-height: 1.7; }
</style>
""", unsafe_allow_html=True)


# EN-TÊTE
st.markdown("""
<div class="hero-banner">
    <h2 class="hero-title"> 🩺 OncoScan <span>AI </span></h2>
    <p class="hero-subtitle">
        Renseignez vos informations médicales et obtenez une évaluation
        instantanée du risque de malignité via notre modèle IA.
    </p>
</div>
""", unsafe_allow_html=True)


# INITIALISATION SÉCURISÉE DE LA VARIABLE SUBMITTED
submitted = False

# FORMULAIRE DE COLLECTE
with st.form(key="oncoscan_form", clear_on_submit=False):

    st.markdown("""
    <div class="form-header">
        <div class="form-header-dot"></div>
        <p class="form-header-text"> Données médicales (valeurs Extrêmes)</p>
    </div>
    """, unsafe_allow_html=True)

    inputs = {}
    col1, col2 = st.columns(2, gap="medium")
    features_list = list(FEATURES_META.items())

    for idx, (feature_key, meta) in enumerate(features_list):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            inputs[feature_key] = st.number_input(
                label=f"{meta['label']}",
                min_value=meta["min"],
                max_value=meta["max"],
                value=meta["default"],
                format=meta["format"],
                key=feature_key,
            )

    st.markdown(
        "<div style='margin-top:0.4rem'></div>",
        unsafe_allow_html=True)
    st.caption(
        "⚠️ Outil d'aide à la décision clinique — ne remplace pas l'avis d'un professionnel de santé.")

    # Attribution de la variable à l'intérieur du formulaire
    submitted = st.form_submit_button(
        label="Lancer l'analyse",
        use_container_width=True,
    )


# CONTENEUR DE SORTIE
output_container = st.container()


# APPEL DE L'API REST
if submitted:
    with output_container:
        with st.spinner("Résultats en cours…"):
            try:
                response = http_client.post(API_URL, json=inputs, timeout=10)
                response.raise_for_status()
                result = response.json()

                pred = result.get("prediction", "unknown")
                prob_malignant = float(result.get(
                    "probability_malignant", 0.0))
                is_malignant = str(pred).strip().lower() in {
                    "m", "malignant", "malin", "maligne"}

                st.markdown(
                    "<div style='margin-top:1.2rem'></div>",
                    unsafe_allow_html=True)

                if is_malignant:
                    prob_pct = prob_malignant * 100
                    st.markdown(f"""
                    <div class="result-card result-malignant">
                        <p class="result-label">⚠️ Diagnostic</p>
                        <p class="result-title">Tumeur Maligne — Risque Élevé</p>
                        <div class="result-prob-row">
                            <span class="result-prob">{prob_pct:.1f}%</span>
                            <span class="result-prob-label">probabilité de malignité</span>
                        </div>
                        <div class="prob-bar-wrap">
                            <div class="prob-bar-fill prob-bar-malignant" style="width:{prob_pct:.1f}%"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    prob_benign_pct = (1.0 - prob_malignant) * 100
                    gauge_fill_pct = prob_malignant * 100

                    st.markdown(f"""
                    <div class="result-card result-benign">
                        <p class="result-label">✅ Diagnostic</p>
                        <p class="result-title">Tumeur Bénigne — Risque Faible</p>
                        <div class="result-prob-row">
                            <span class="result-prob">{prob_benign_pct:.1f}%</span>
                            <span class="result-prob-label">probabilité de bénignité</span>
                        </div>
                        <div class="prob-bar-wrap">
                            <div class="prob-bar-fill prob-bar-benign" style="width:{gauge_fill_pct:.1f}%"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            except requests.exceptions.ConnectionError:
                st.error(
                    "**Erreur de connexion** — Impossible de joindre l'API OncoScan. Vérifiez que le conteneur API FastAPI est démarré.")
            except requests.exceptions.Timeout:
                st.error(
                    "**Délai dépassé** — L'API n'a pas répondu dans le délai imparti.")
            except requests.exceptions.HTTPError as http_err:
                st.error(
                    f"**Erreur HTTP {response.status_code}** — Détail : `{http_err}`")
            except (KeyError, ValueError) as parse_err:
                st.error(
                    f"**Erreur de parsing** — Format de réponse inattendu : `{parse_err}`")


# PIED DE PAGE INTERFACE
st.markdown("""
<div class="app-footer">
    OncoScan AI · Modèle entraîné sur le <em>Wisconsin Breast Cancer Dataset</em> (kaggle)<br>
    À usage de démonstration uniquement — non certifié CE/FDA · © 2026 OncoScan AI<br>
    Auteur : @Madiba
</div>
""", unsafe_allow_html=True)
