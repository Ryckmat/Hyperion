"""
Module de monitoring et métriques qualité pour le système RAG

Composants:
- QualityMetricsTracker: Collecte et agrégation des métriques
- DashboardData: Formatage données pour dashboard
"""

from .quality_metrics import QualityMetricsTracker

__all__ = ["QualityMetricsTracker"]

__version__ = "2.8.0"
