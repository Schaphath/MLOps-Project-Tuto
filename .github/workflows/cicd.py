name: CI/CD OncoScan AI

on:
  push:
    branches: ["main", "develop"]
  pull_request:
    branches: ["main"]

jobs:
  # =======================================#
  # ÉTAPE 1 : QUALITÉ DU CODE (Linting)    #
  # =======================================#
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install linter
        run: pip install flake8

      # Ajustement : Pointage ciblé sur tes scripts réels et leurs sous-dossiers
      - name: Lint API
        run: flake8 Api/main.py --max-line-length=120 --ignore=E501,W503

      - name: Lint Streamlit
        run: flake8 Interface/app.py --max-line-length=120 --ignore=E501,W503

  # ==========================================================#
  # ÉTAPE 2 : TESTS UNITAIRES (Conteneur Postgres éphémère)   #
  # ==========================================================#
  test:
    needs: lint
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: oncoscan
          POSTGRES_USER: oncoscan
          POSTGRES_PASSWORD: oncoscan_secure_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U oncoscan"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('requirements-prod.txt') }}
          restore-keys: |
            pip-

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements-prod.txt
          pip install pytest httpx pytest-asyncio

      # Ajustement : Pointage sur le sous-dossier database pour trouver ton init.sql
      - name: Init database
        env:
          PGPASSWORD: oncoscan_secure_password
        run: |
          psql -h localhost -U oncoscan -d oncoscan -f database/init.sql

      - name: Run tests
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: oncoscan
          DB_USER: oncoscan
          DB_PASSWORD: oncoscan_secure_password
        run: |
          pytest tests/ -v --junitxml=test-results.xml

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results.xml

  # ===========================================================================
  # ÉTAPE 3 : COMPILATION & LIVRAISON (Docker Hub - Uniquement sur Main)
  # ===========================================================================
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

      - name: Set image tag
        id: tag
        run: echo "SHA=$(echo $GITHUB_SHA | cut -c1-7)" >> $GITHUB_OUTPUT

      # Ajustement : Contexte racine (.) et ciblage du Dockerfile dans ./Api/
      - name: Build and Push API
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Api/Dockerfile
          target: runtime
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/oncoscan-api:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/oncoscan-api:${{ steps.tag.outputs.SHA }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      # Ajustement : Contexte racine (.) et ciblage du Dockerfile dans ./Interface/
      - name: Build and Push Streamlit
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Interface/Dockerfile
          target: runtime
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/oncoscan-streamlit:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/oncoscan-streamlit:${{ steps.tag.outputs.SHA }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ===========================================================================
  # ÉTAPE 4 : NOTIFICATION RÉSUMÉ (S'exécute toujours à la fin)
  # ===========================================================================
  notify:
    needs: [lint, test, build-and-push]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Résumé du pipeline
        run: |
          echo "=== RÉSUMÉ DU PIPELINE ONCOSCAN ==="
          echo "Commit  : $GITHUB_SHA"
          echo "Branche : $GITHUB_REF_NAME"
          echo "Statut global complété."