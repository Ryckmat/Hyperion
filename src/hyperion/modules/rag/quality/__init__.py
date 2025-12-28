"""
Module de validation qualité des réponses RAG

Ce module contient les composants pour la détection d'hallucinations
et la validation de la qualité des réponses générées par le système RAG.

Composants:
- HallucinationDetector: Détection des hallucinations multi-niveaux
- ConfidenceScorer: Calcul de scores de confiance
- ResponseValidator: Orchestrateur de validation
- QualityMetrics: Tracking et métriques qualité
"""

from .hallucination_detector import HallucinationDetector
from .confidence_scorer import ConfidenceScorer
from .response_validator import ResponseValidator

__all__ = [
    'HallucinationDetector',
    'ConfidenceScorer',
    'ResponseValidator'
]

__version__ = "2.8.0"