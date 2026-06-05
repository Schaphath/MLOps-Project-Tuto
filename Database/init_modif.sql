-- Nettoyage de sécurité lors de l'initialisation
DROP TABLE IF EXISTS predictions CASCADE;

-- =============================================================================
-- TABLE DES PRÉDICTIONS (Historique anonyme des analyses de l'API)
-- =============================================================================
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    
    -- Les 8 caractéristiques cellulaires utilisées par le modèle (Validation stricte)
    texture_worst FLOAT NOT NULL CONSTRAINT chk_texture_worst CHECK (texture_worst > 0),
    area_worst FLOAT NOT NULL CONSTRAINT chk_area_worst CHECK (area_worst > 0),
    smoothness_worst FLOAT NOT NULL CONSTRAINT chk_smoothness_worst CHECK (smoothness_worst > 0),
    compactness_worst FLOAT NOT NULL CONSTRAINT chk_compactness_worst CHECK (compactness_worst >= 0),
    concavity_worst FLOAT NOT NULL CONSTRAINT chk_concavity_worst CHECK (concavity_worst >= 0),
    concave_points_worst FLOAT NOT NULL CONSTRAINT chk_concave_points_worst CHECK (concave_points_worst >= 0),
    symmetry_worst FLOAT NOT NULL CONSTRAINT chk_symmetry_worst CHECK (symmetry_worst > 0),
    fractal_dimension_worst FLOAT NOT NULL CONSTRAINT chk_fractal_dimension_worst CHECK (fractal_dimension_worst > 0),
    
    -- Résultats de l'inférence
    prediction VARCHAR(2) NOT NULL CONSTRAINT chk_prediction_format CHECK (prediction IN ('M', 'B')),
    probability_pct FLOAT NOT NULL CONSTRAINT chk_probability_range CHECK (probability_pct BETWEEN 0.0 AND 100.0),
    
    -- Métadonnées de tracking
    date_analyse TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEX DE PRODUCTION (Optimisation des requêtes de monitoring et d'audit)
-- =============================================================================
-- Index pour accélérer le filtrage chronologique (ex: extraire les analyses du mois)
CREATE INDEX idx_predictions_date ON predictions (date_analyse DESC);

-- Index pour accélérer le requêtage par classe diagnostique (ex: ratio Maligne/Bénigne)
CREATE INDEX idx_predictions_label ON predictions (prediction);