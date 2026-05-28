```markdown
# 🩺 OncoScan AI : Pipeline MLOps d'Aide au Diagnostic Oncologique

[![CI/CD Pipeline](https://github.com/votre-username/oncoscan-ai/actions/workflows/cicd.yml/badge.svg)](https://github.com/votre-username/oncoscan-ai/actions)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📌 Présentation

OncoScan AI industrialise la classification tumeurs mammaires (malin/bénin) via une architecture microservices avec CI/CD complet — outil d'aide à la décision standardisé, sécurisé et auditable.

## 🔬 Données & Modèle

- **Features clés** : `area_worst`, `concave_points_worst`, `texture_worst`, `concavity_worst`
- **Preprocessing** : MinMaxScaler
- **Algorithme** : XGBoost Classifier optimisé pour maximiser le rappel (minimiser faux négatifs)

## 🛠 Stack

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| API | FastAPI + Uvicorn | Inférence REST |
| UI | Streamlit | Interface praticien |
| Base | PostgreSQL 15 | Historique & utilisateurs |
| Conteneurisation | Docker + Compose | Multi-stage builds |
| CI/CD | GitHub Actions | Linting, tests, déploiement |

## 🏗 Architecture

```
Client → Streamlit (8501) ──port 5432──→ PostgreSQL
                        └──port 8000──→ FastAPI (isolé de la DB)
```

**Flux** : Auth/Historique via Streamlit → PostgreSQL. Prédiction via Streamlit → API → retour JSON.

## 📂 Structure

```
├── .github/workflows/cicd.yml
├── Api/
│   ├── api.py
│   └── Dockerfile
├── Interface/
│   ├── app_stream.py
│   └── Dockerfile
├── database/init.sql
├── Save_models/
│   ├── xgboost_best.pkl
│   └── MinMax_scaler.pkl
├── requirements-prod.txt
├── requirements-streamlit.txt
└── docker-compose.yml
```

## 🚀 Lancement

```bash
docker compose up --build -d
```

- UI : `http://localhost:8501`
- API Docs : `http://localhost:8000/docs`
- Health : `http://localhost:8000/health`

## ⚙️ CI/CD

- **Linting** : Flake8
- **Tests** : Pytest + httpx + PostgreSQL éphémère
- **CD** : Push sur `main` → build & push images Docker Hub (tag `latest` + `sha-7`)

**Secrets requis** : `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
```