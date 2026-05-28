-- =============================================================================
-- NETTOYAGE DES ANCIENNES TABLES (Optionnel, idéal pour le développement)
-- =============================================================================
DROP TABLE IF EXISTS predictions;
DROP TABLE IF EXISTS users;

-- =============================================================================
-- 1. TABLE DES UTILISATEURS (Praticiens / Enseignants)
-- =============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(64) NOT NULL, -- Stockage du hash SHA-256 (64 caractères)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 2. TABLE DES PRÉDICTIONS (Historique des analyses de l'API)
-- =============================================================================
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    utilisateur VARCHAR(50) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    
    -- Les 8 caractéristiques cellulaires utilisées par le modèle XGBoost
    texture_worst FLOAT NOT NULL,
    area_worst FLOAT NOT NULL,
    smoothness_worst FLOAT NOT NULL,
    compactness_worst FLOAT NOT NULL,
    concavity_worst FLOAT NOT NULL,
    concave_points_worst FLOAT NOT NULL,
    symmetry_worst FLOAT NOT NULL,
    fractal_dimension_worst FLOAT NOT NULL,
    
    -- Résultats de l'inférence
    prediction VARCHAR(2) NOT NULL,       -- 'M' (Maligne) ou 'B' (Bénigne)
    probability_pct FLOAT NOT NULL,       -- Probabilité convertie en pourcentage (0 à 100)
    
    date_analyse TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXATION OPTIMISÉE (Meilleure pratique pour la production)
-- =============================================================================
-- Accélère la recherche de l'historique lorsqu'un praticien se connecte
CREATE INDEX idx_predictions_utilisateur ON predictions(utilisateur);