<<<<<<< Updated upstream

=======
<div align="center">

<!-- LOGO / BANNER -->
<img src="https://img.shields.io/badge/-%F0%9F%A9%BA%20OncoScan%20AI-0a0a0a?style=for-the-badge&logoColor=white" alt="OncoScan AI" height="60"/>



### Pipeline MLOps d'Aide au Diagnostic Oncologique

*Classification automatisée de tumeurs mammaires*

<br/>

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-Classifier-orange)](https://xgboost.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<br/>

[📖 Documentation API](#-api--endpoints) · [🚀 Démarrage rapide](#-démarrage-rapide) · [🏗 Architecture](#-architecture) · [🤝 Contribuer](#-contribuer)

</div>

---

## 📌 Vue d'ensemble

**OncoScan AI** est un pipeline MLOps de bout en bout conçu pour **industrialiser la classification de tumeurs mammaires** (malin / bénin) à partir de caractéristiques morphologiques cellulaires.

Le projet met en œuvre une architecture microservices complète avec CI/CD automatisé — pour fournir aux praticiens un outil d'aide à la décision **standardisé, sécurisé, traçable et auditable**.

> ⚠️ **Avertissement médical** : OncoScan AI est un outil d'aide à la décision clinique. Il ne remplace en aucun cas le jugement d'un professionnel de santé qualifié.

### ✨ Points forts

| | |
|---|---|
| 🎯 **Précision clinique** | Optimisé pour maximiser le rappel (minimiser les faux négatifs) |
| 🔐 **Sécurisé** | Authentification utilisateur, historique des prédictions auditable |
| 📦 **Prêt production** | Conteneurisé Docker, multi-stage builds, health checks |
| ⚡ **CI/CD complet** | Linting → Tests → Build → Push automatisés sur chaque commit |
| 📊 **Explicable** | Features importantes documentées, résultats interprétables |

---

## 🔬 Données & Modèle

### Dataset

Le modèle est entraîné sur le **Wisconsin Breast Cancer Dataset (WBCD)**, un benchmark reconnu en oncologie computationnelle.

- **569 observations** · 30 features morphologiques · 2 classes (M / B)
- **Ratio** : ~63% bénin / ~37% malin

### Features sélectionnées

| Feature | Description | Importance |
|---------|-------------|-----------|
| `area_worst` | Aire maximale du noyau cellulaire | ⭐⭐⭐⭐⭐ |
| `concave_points_worst` | Nb de points concaves (pire cas) | ⭐⭐⭐⭐⭐ |
| `concavity_worst` | Sévérité des concavités (pire cas) | ⭐⭐⭐⭐ |
| `texture_worst` | Écart-type des niveaux de gris (pire cas) | ⭐⭐⭐ |

### Pipeline de modélisation

```
Données brutes → MinMaxScaler → XGBoost Classifier → Prédiction (M/B) + Probabilité
```

- **Preprocessing** : `MinMaxScaler` (séralisé `MinMax_scaler.pkl`)
- **Algorithme** : `XGBoostClassifier` (sérialisé `xgboost_best.pkl`)
- **Optimisation** : Maximisation du rappel (`recall`) sur la classe maligne pour limiter les faux négatifs

---

## 🏗 Architecture

### Vue d'ensemble des services

```
┌─────────────────────────────────────────────────────────┐
│                        CLIENT                           │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP
                        ▼
┌───────────────────────────────────────────────────────┐
│            Streamlit UI  :8501                        │
│         (Authentification · Saisie · Historique)      │
└───────┬──────────────────────────┬────────────────────┘
        │ HTTP REST                │ SQL (port 5432)
        ▼                          ▼
┌───────────────┐       ┌──────────────────────┐
│  FastAPI      │       │   PostgreSQL 15       │
│  :8000        │       │                      │
│  (Inférence)  │       │  · users             │
│               │       │  · predictions       │
└───────────────┘       └──────────────────────┘
  ↑ Isolé de la DB
```

### Flux de données

```
1. [Utilisateur]  →  S'authentifie via Streamlit → PostgreSQL
2. [Utilisateur]  →  Saisit les mesures cliniques dans Streamlit
3. [Streamlit]    →  POST /predict → FastAPI
4. [FastAPI]      →  Charge scaler + modèle → retourne JSON {prediction, probability}
5. [Streamlit]    →  Affiche résultat + sauvegarde dans PostgreSQL (historique)
```

### Isolation des services

- **FastAPI** n'a pas accès direct à PostgreSQL → séparation des responsabilités
- **Streamlit** orchestre : gère auth, historique (DB) et inférence (API)
- Chaque service dispose de son propre `Dockerfile` multi-stage

---

## 🛠 Stack technique

| Couche | Technologie | Version | Rôle |
|--------|-------------|---------|------|
| **API d'inférence** | FastAPI + Uvicorn | 0.111+ | Endpoints REST, prédiction ML |
| **Interface praticien** | Streamlit | 1.x | UI clinique, auth, historique |
| **Base de données** | PostgreSQL | 15 | Utilisateurs & logs prédictions |
| **ML** | XGBoost | latest | Classificateur tumeurs |
| **Preprocessing** | scikit-learn | latest | MinMaxScaler |
| **Conteneurisation** | Docker + Compose | latest | Multi-stage, isolation réseau |
| **CI/CD** | GitHub Actions | - | Lint → Test → Build → Push |
| **Linting** | Flake8 | - | Qualité du code |
| **Tests** | Pytest + httpx | - | Tests API avec DB éphémère |

---

## 📂 Structure du projet

```
oncoscan-ai/
│
├── .github/
│   └── workflows/
│       └── cicd.yml              # Pipeline CI/CD complet
│
├── Api/
│   ├── api.py                    # Application FastAPI (routes + logique inférence)
│   └── Dockerfile                # Image multi-stage de l'API
│
├── Interface/
│   ├── app_stream.py             # Application Streamlit (UI + auth + historique)
│   └── Dockerfile                # Image multi-stage de l'interface
│
├── database/
│   └── init.sql                  # Schéma PostgreSQL (users, predictions)
│
├── Save_models/
│   ├── xgboost_best.pkl          # Modèle XGBoost entraîné et sérialisé
│   └── MinMax_scaler.pkl         # Scaler sérialisé
│
├── tests/                        # Suite de tests Pytest
│   └── test_api.py
│
├── requirements-prod.txt         # Dépendances API
├── requirements-streamlit.txt    # Dépendances Interface
├── docker-compose.yml            # Orchestration multi-services
└── README.md
```

---

## 🚀 Démarrage rapide

### Prérequis

- [Docker](https://docs.docker.com/get-docker/) ≥ 24.x
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.x

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-username/oncoscan-ai.git
cd oncoscan-ai
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditez .env avec vos paramètres (DB password, secret key...)
```

### 3. Lancer tous les services

```bash
docker compose up --build -d
```

### 4. Accéder aux interfaces

| Service | URL | Description |
|---------|-----|-------------|
| 🖥️ Interface praticien | http://localhost:8501 | UI Streamlit |
| 📚 Documentation API | http://localhost:8000/docs | Swagger UI |
| ❤️ Health check API | http://localhost:8000/health | Statut du service |

### 5. Arrêter les services

```bash
docker compose down          # Arrêt simple
docker compose down -v       # Arrêt + suppression des volumes
```

---

## 📡 API — Endpoints

### `GET /health`

Vérifie que l'API est opérationnelle.

```json
// Response 200 OK
{
  "status": "healthy",
  "model": "loaded",
  "version": "1.0.0"
}
```

### `POST /predict`

Réalise une prédiction à partir des features morphologiques.

**Request body :**

```json
{
  "area_worst": 1001.0,
  "concave_points_worst": 0.1471,
  "texture_worst": 17.33,
  "concavity_worst": 0.2654
}
```

**Response :**

```json
{
  "prediction": "Malignant",
  "probability": 0.923,
  "label": 1
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `prediction` | `string` | `"Malignant"` ou `"Benign"` |
| `probability` | `float` | Probabilité de malignité [0, 1] |
| `label` | `int` | `1` = Malin, `0` = Bénin |

---

## ⚙️ Pipeline CI/CD

Le pipeline GitHub Actions s'exécute automatiquement sur chaque **push** et **pull request** sur `main`.

```
Push / PR sur main
        │
        ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐
│   Linting    │ →  │    Tests     │ →  │   Build & Push       │
│   (Flake8)   │    │  (Pytest +   │    │  Docker Hub          │
│              │    │   httpx +    │    │  :latest + :sha-7    │
│              │    │   PG éphém.) │    │  (sur main seulement)│
└──────────────┘    └──────────────┘    └──────────────────────┘
```

### Secrets GitHub requis

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Votre identifiant Docker Hub |
| `DOCKERHUB_TOKEN` | Token d'accès Docker Hub (pas votre mot de passe) |

### Tags d'images produits

- `votre-username/oncoscan-api:latest`
- `votre-username/oncoscan-api:sha-a1b2c3d` *(7 premiers caractères du commit)*
- `votre-username/oncoscan-ui:latest`
- `votre-username/oncoscan-ui:sha-a1b2c3d`

---

## 🧪 Tests en local

```bash
# Installer les dépendances de test
pip install pytest httpx

# Lancer les tests (nécessite une instance PostgreSQL locale ou via Docker)
pytest tests/ -v

# Avec couverture de code
pytest tests/ -v --cov=Api --cov-report=term-missing
```

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! Voici comment participer :

1. **Forkez** le dépôt
2. **Créez** une branche feature (`git checkout -b feature/ma-feature`)
3. **Committez** vos changements (`git commit -m 'feat: ajouter ma feature'`)
4. **Poussez** sur la branche (`git push origin feature/ma-feature`)
5. **Ouvrez** une Pull Request

Merci de respecter les conventions de commit [Conventional Commits](https://www.conventionalcommits.org/) et de vous assurer que les tests passent avant de soumettre une PR.

---

## 📄 Licence

Ce projet est distribué sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus d'informations.

---

<div align="center">

Fait avec ❤️ pour la recherche en oncologie computationnelle

⭐ **N'hésitez pas à étoiler ce dépôt si le projet vous est utile !** ⭐

</div>
>>>>>>> Stashed changes
