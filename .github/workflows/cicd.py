name: CI/CD OncoScan AI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  
  # =============================================================================
  # ÉTAPE 1 : QUALITÉ DU CODE & INTEGRITÉ DES ARTEFACTS
  # =============================================================================
  lint-and-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install linter
        run: pip install flake8

      # Vérification des scripts corrigés
      - name: Lint API Code
        run: flake8 api_modif.py --max-line-length=120 --ignore=E501,W503

      - name: Lint Streamlit Interface
        run: flake8 interface.py --max-line-length=120 --ignore=E501,W503

      # S'assurer que les fichiers du modèle ne manquent pas
      - name: Verify ML Artifacts Existence
        run: |
          if [ ! -f "Save_models/xgboost_best.pkl" ] || [ ! -f "Save_models/MinMax_scaler.pkl" ]; then
            echo "Erreur critique : Les fichiers xgboost_best.pkl ou MinMax_scaler.pkl sont manquants dans Save_models/"
            exit 1
          fi
          echo "Modèle XGBoost et Scaler validés."


  # =============================================================================
  # ÉTAPE 2 : TESTS UNITAIRES & INTEGRATION (Conteneur Postgres éphémère)
  # =============================================================================
  test:
    needs: lint-and-validate
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: oncoscan_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres_secure_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres -d oncoscan_db"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # Optimisation : Clé de cache pour surveiller les dépendances
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('requirements-prod.txt', 'requirements-streamlit.txt') }}
          restore-keys: |
            pip-

      # Installation de l'ensemble de l'écosystème nécessaire aux tests d'intégration
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements-prod.txt ]; then pip install -r requirements-prod.txt; fi
          if [ -f requirements-streamlit.txt ]; then pip install -r requirements-streamlit.txt; fi
          pip install pytest httpx pytest-asyncio

      - name: Init database schema
        env:
          PGPASSWORD: postgres_secure_password
        run: |
          # Vérification de l'existence du script SQL d'initialisation avant exécution
          if [ -f Database/init_modif.sql ]; then
            psql -h localhost -U postgres -d oncoscan_db -f Database/init_modif.sql
          else
            echo "Fichier Database/init_modif.sql introuvable."
          fi

      - name: Run Pytest Suite
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: oncoscan_db
          DB_USER: postgres
          DB_PASSWORD: postgres_secure_password
        run: |
          # FIX : Création explicite du dossier pour éviter le FileNotFoundError de Pytest
          mkdir -p Tests_results
          
          # Exécution et centralisation des rapports XML
          pytest tests/ -v --junitxml=Tests_results/integration-results.xml
          pytest Tests/test_model.py -v --junitxml=Tests_results/model-results.xml 
          
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: Tests_results/


  # =============================================================================
  # ÉTAPE 3 : COMPILATION & LIVRAISON (Docker Hub - Uniquement sur Main)
  # =============================================================================
  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Set image tag (Short SHA)
        id: tag
        run: echo "SHA=$(echo $GITHUB_SHA | cut -c1-7)" >> $GITHUB_OUTPUT

      - name: Build and Push API (FastAPI)
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Api/Dockerfile
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/oncoscan-api:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/oncoscan-api:${{ steps.tag.outputs.SHA }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and Push Streamlit Interface
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Interface/Dockerfile
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/oncoscan-streamlit:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/oncoscan-streamlit:${{ steps.tag.outputs.SHA }}
          cache-from: type=gha
          cache-to: type=gha,mode=max


  # =============================================================================
  # ÉTAPE 4 : NOTIFICATION ET RÉSUMÉ DE PIPELINE
  # =============================================================================
  notify:
    needs: [lint-and-validate, test, build-and-push]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Résumé exécutif
        run: |
          echo "=== RÉSUMÉ DU PIPELINE GITHUB ACTIONS ==="
          echo "Commit ID : $GITHUB_SHA"
          echo "Branche   : $GITHUB_REF_NAME"
          echo "Vérifications de code et déploiement Docker complétés."