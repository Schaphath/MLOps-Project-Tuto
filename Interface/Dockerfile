# ==========================================
# ÉTAPE 1 : BUILDER (Installation isolée)
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Copie uniquement le fichier des dépendances
COPY requirements-streamlit.txt .

# Installation des paquets requis pour l'interface
# psycopg2-binary est utilisé pour éviter d'installer les outils de compilation de postgres (gcc)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user streamlit requests psycopg2-binary

# ===============================================
# ÉTAPE 2 : RUNTIME (Image finale ultra-légère)
# ===============================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Sécurité : Création d'un utilisateur non-root pour l'exécution
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Récupération uniquement des dépendances installées à l'étape 1
COPY --from=builder /root/.local /home/appuser/.local

# Copie du code de l'interface Streamlit
COPY --chown=appuser:appuser ./Interface/app_stream.py .

# Configuration des variables d'environnement indispensables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Passage sous l'utilisateur sécurisé
USER appuser

# Port par défaut utilisé par Streamlit
EXPOSE 8501

# Commande de lancement de production pour Streamlit
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]