# ÉTAPE 1 : BUILDER 
FROM python:3.12-slim AS builder

WORKDIR /app

# Copier le fichier requirements-streamlit.txt
COPY requirements-streamlit.txt .

# Installation des packages dans le fichier requirements-streamlit.txt 
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements-streamlit.txt
    

# ÉTAPE 2 : RUNTIME
FROM python:3.12-slim AS runtime

WORKDIR /app

# Création d'un utilisateur non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Récupération des dépendances installées à l'étape 1
COPY --from=builder /root/.local /home/appuser/.local

COPY --chown=appuser:appuser ./Interface/interface.py ./interface.py


# Variables d'environnement indispensables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Passage sous l'utilisateur sécurisé
USER appuser

# Port découte Streamlit
EXPOSE 8501

# Lancement de l'interface web
CMD ["streamlit", "run", "interface.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
