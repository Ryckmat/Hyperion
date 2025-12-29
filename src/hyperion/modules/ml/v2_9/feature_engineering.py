"""
Hyperion v2.9 - Feature Engineering
Ingénierie des features pour les modèles ML
"""

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration pour feature engineering"""

    normalize: bool = True
    scale: bool = True
    feature_selection: bool = True


class FeatureEngineer:
    """Ingénieur des features"""

    def __init__(self, config: FeatureConfig = None):
        self.config = config or FeatureConfig()

    def transform_features(self, X: np.ndarray) -> np.ndarray:
        """Transforme les features"""
        if self.config.normalize:
            X = self._normalize(X)
        if self.config.scale:
            X = self._scale(X)
        return X

    def _normalize(self, X: np.ndarray) -> np.ndarray:
        """Normalisation simple"""
        return (X - np.mean(X, axis=0)) / (np.std(X, axis=0) + 1e-8)

    def _scale(self, X: np.ndarray) -> np.ndarray:
        """Mise à l'échelle"""
        return (X - np.min(X, axis=0)) / (np.max(X, axis=0) - np.min(X, axis=0) + 1e-8)


class AdvancedFeatureEngineer(FeatureEngineer):
    """Ingénieur de features avancé pour ML enterprise"""

    def __init__(self, config: FeatureConfig = None):
        super().__init__(config)
        self.feature_cache = {}
        self.feature_importance = {}

    def engineer_advanced_features(self, X: np.ndarray) -> np.ndarray:
        """Génère des features avancées"""
        # Features polynomiales
        poly_features = self._create_polynomial_features(X)

        # Features d'interaction
        interaction_features = self._create_interaction_features(X)

        # Combiner toutes les features
        advanced_X = np.hstack([X, poly_features, interaction_features])

        return self.transform_features(advanced_X)

    def _create_polynomial_features(self, X: np.ndarray, degree: int = 2) -> np.ndarray:
        """Crée des features polynomiales"""
        if X.shape[1] > 10:  # Limiter pour éviter explosion combinatoire
            return X[:, :5] ** degree
        return X**degree

    def _create_interaction_features(self, X: np.ndarray) -> np.ndarray:
        """Crée des features d'interaction"""
        n_samples, n_features = X.shape
        if n_features < 2:
            return np.zeros((n_samples, 1))

        # Interactions 2 à 2 pour les premières features
        max_interactions = min(n_features, 5)
        interactions = []

        for i in range(max_interactions - 1):
            for j in range(i + 1, max_interactions):
                interaction = X[:, i] * X[:, j]
                interactions.append(interaction.reshape(-1, 1))

        if interactions:
            return np.hstack(interactions)
        return np.zeros((n_samples, 1))

    def select_features(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """Sélection de features basée sur l'importance"""
        if y is None:
            # Sélection sans supervision - variance
            variances = np.var(X, axis=0)
            threshold = np.percentile(variances, 75)  # Top 25%
            selected_indices = variances > threshold
            return X[:, selected_indices]

        # Sélection supervisée - corrélation simple
        correlations = []
        for i in range(X.shape[1]):
            corr = abs(np.corrcoef(X[:, i], y)[0, 1])
            if np.isnan(corr):
                corr = 0
            correlations.append(corr)

        correlations = np.array(correlations)
        threshold = np.percentile(correlations, 70)  # Top 30%
        selected_indices = correlations > threshold

        return X[:, selected_indices]

    def get_feature_importance(self) -> dict[str, float]:
        """Retourne l'importance des features"""
        return self.feature_importance.copy()


# Instances globales
default_feature_engineer = FeatureEngineer()
advanced_feature_engineer = AdvancedFeatureEngineer()
