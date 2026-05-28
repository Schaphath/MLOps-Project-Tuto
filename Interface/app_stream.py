import os
import hashlib
import requests
import streamlit as st
import psycopg2

# Configuration des variables d'environnement (Production / Docker)
API_URL = os.getenv("API_URL", "http://api:8000/predict")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "oncoscan"),
    "user": os.getenv("DB_USER", "oncoscan"),
    "password": os.getenv("DB_PASSWORD", "oncoscan"),
}

# Liste des caractéristiques (features) de la tumeur
FEATURES = [
    "texture_worst", "area_worst", "smoothness_worst", "compactness_worst",
    "concavity_worst", "concave_points_worst", "symmetry_worst", "fractal_dimension_worst"
]

# Gestion de la connexion PostgreSQL (Context Manager automatique)
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

#--- INITIALISATION DU SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

st.title("🩺 OncoScan AI")

#====================================================#
# 1. ÉCRAN D'AUTHENTIFICATION (Si non connecté)      #
#====================================================#
if not st.session_state.authenticated:
    tab_login, tab_register = st.tabs(["Connexion", "Création de compte"])
    
    with tab_login:
        user = st.text_input("Identifiant", key="l_user").strip().lower()
        pwd = st.text_input("Mot de passe", type="password", key="l_pwd")
        
        if st.button("Se connecter", use_container_width=True):
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT password FROM users WHERE username = %s", (user,))
                        row = cur.fetchone()
                        
                if row and row[0] == hash_password(pwd):
                    st.session_state.authenticated = True
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
            except Exception as e:
                st.error(f"Erreur de connexion à la base de données : {e}")

    with tab_register:
        new_user = st.text_input("Choisir un identifiant", key="r_user").strip().lower()
        new_pwd = st.text_input("Choisir un mot de passe", type="password", key="r_pwd")
        
        if st.button("Créer le compte", use_container_width=True):
            if len(new_user) < 3 or len(new_pwd) < 6:
                st.warning("Identifiant (min. 3 car.) ou mot de passe (min. 6 car.) trop court.")
            else:
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_user, hash_password(new_pwd)))
                        conn.commit()
                        
                    st.success("Compte créé avec succès ! Connectez-vous via l'onglet dédié.")
                except psycopg2.errors.UniqueViolation:
                    st.error("Cet identifiant existe déjà.")
                except Exception as e:
                    st.error(f"Erreur lors de l'inscription : {e}")
    st.stop()

#=============================================#
# 2. APPLICATION PRINCIPALE (Si connecté)     #
#=============================================#
st.sidebar.write(f"Praticien : **{st.session_state.username}**")
if st.sidebar.button("Déconnexion"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

st.subheader("Analyse des Caractéristiques Cellulaires ('Worst')")

# Génération dynamique du formulaire de saisie
inputs = {}
col1, col2 = st.columns(2)
for idx, feature in enumerate(FEATURES):
    target_col = col1 if idx % 2 == 0 else col2
    with target_col:
        inputs[feature] = st.number_input(
            label=feature.replace("_", " ").title(),
            min_value=0.0001,
            max_value=2500.0,
            format="%.4f",
            key=feature
        )

# Soumission du formulaire et traitement des requêtes
if st.button("Lancer l'analyse du risque", use_container_width=True):
    with st.spinner("Inférence en cours via l'API..."):
        try:
            # 1. Envoi des données à l'API FastAPI
            response = requests.post(API_URL, json=inputs, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                pred = result["prediction"]
                prob = result["probability_malignant"]
                
                # 2. Sauvegarde immédiate dans l'historique PostgreSQL
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO predictions (
                                    utilisateur, texture_worst, area_worst, smoothness_worst, 
                                    compactness_worst, concavity_worst, concave_points_worst, 
                                    symmetry_worst, fractal_dimension_worst, prediction, probability_pct
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                st.session_state.username, inputs["texture_worst"], inputs["area_worst"],
                                inputs["smoothness_worst"], inputs["compactness_worst"], inputs["concavity_worst"],
                                inputs["concave_points_worst"], inputs["symmetry_worst"], inputs["fractal_dimension_worst"],
                                pred, round(prob * 100, 2)
                            ))
                        conn.commit()
                except Exception as db_err:
                    st.warning(f"Impossible d'enregistrer dans l'historique : {db_err}")

                # 3. Affichage visuel du diagnostic médical
                if pred == "M":
                    st.error(f"🚨 TUMEUR MALIGNE (Risque Élevé) — Probabilité : {prob * 100:.2f}%")
                    st.info("💡 **Recommandation :** Une confrontation anatomopathologique (biopsie) est requise.")
                else:
                    st.success(f"✓ TUMEUR BÉNIGNE (Risque Faible) — Probabilité : {prob * 100:.2f}%")
            else:
                st.error(f"L'API a renvoyé une erreur (Code {response.status_code})")
                
        except requests.exceptions.RequestException as net_err:
            st.error(f"Erreur réseau : Impossible de contacter l'API de prédiction. {net_err}")
