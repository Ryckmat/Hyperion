"""
Modules Machine Learning Avancés - Hyperion v3.0 Enterprise.

Ce package contient l'infrastructure ML complète pour:
- Prédiction de risque avancée (ensemble de modèles)
- Prédiction de bugs basée sur historique
- Détection de code smells par ML
- Pipeline d'entraînement et validation

Architecture:
- infrastructure/: Registry modèles, configuration, validation données
- training/: Pipeline entraînement, preprocessing, feature engineering
- validation/: Validation modèles, cross-validation, détection biais

Auteur: Équipe Hyperion
Version: 3.0.0-dev
"""

__version__ = "3.0.0-dev"
__author__ = "Équipe Hyperion"

# Imports principaux pour faciliter l'utilisation
from .infrastructure.ml_config import MLConfig
from .infrastructure.model_registry import ModelRegistry

__all__ = [
    "MLConfig",
    "ModelRegistry",
]
