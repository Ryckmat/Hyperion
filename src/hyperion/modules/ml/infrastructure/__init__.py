"""
Infrastructure ML - Configuration, Registry et Validation.

Ce module fournit l'infrastructure de base pour les modèles ML:
- Configuration centralisée ML
- Registry des modèles avec versioning
- Feature store pour persistance features
- Validation données et modèles
"""

from .ml_config import MLConfig
from .model_registry import ModelRegistry

__all__ = [
    "MLConfig",
    "ModelRegistry",
]
