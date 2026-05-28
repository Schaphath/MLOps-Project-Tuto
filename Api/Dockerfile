# ==========================================
# ÉTAPE 1 : BUILDER (Installation isolée)
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Copie uniquement le fichier des dépendances
COPY requirements-prod.txt .

# Installation des paquets dans un dossier local isolé (--user)
# --no-cache-dir évite de stocker des fichiers temporaires et réduit la taille
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements-prod.txt

# ==========================================
# ÉTAPE 2 : RUNTIME (Image finale ultra-légère)
# ==========================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Sécurité : Création d'un utilisateur non-root pour l'exécution
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Récupération uniquement des dépendances installées à l'étape 1
COPY --from=builder /root/.local /home/appuser/.local

# Copie du code de l'API et du dossier des modèles
COPY --chown=appuser:appuser ./Api/api.py .
COPY --chown=appuser:appuser ./Save_models/ ./save_models/

# Configuration des variables d'environnement indispensables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Passage sous l'utilisateur sécurisé
USER appuser

# Port d'écoute de l'API
EXPOSE 8000

# Commande de lancement de production via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]