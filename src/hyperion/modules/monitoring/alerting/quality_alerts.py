"""
Quality-specific Alerts for Hyperion v3.0

Alertes spécialisées pour la qualité RAG et ML avec seuils intelligents.
"""

import logging
from dataclasses import dataclass
from typing import Any

from .alert_manager import AlertCategory, AlertManager, AlertRule, AlertSeverity

logger = logging.getLogger(__name__)


@dataclass
class QualityThresholds:
    """Seuils de qualité configurables"""

    # RAG Quality
    min_relevance_score: float = 0.7
    min_coherence_score: float = 0.6
    max_hallucination_rate: float = 0.15
    min_confidence_score: float = 0.5

    # Response Times
    max_rag_response_time: float = 5.0
    max_ml_inference_time: float = 2.0
    max_api_response_time: float = 1.0

    # Accuracy
    min_ml_accuracy: float = 0.85
    min_citation_accuracy: float = 0.8

    # System Health
    max_error_rate: float = 0.05
    min_success_rate: float = 0.95


class QualityAlerts:
    """
    Système d'alertes spécialisé pour la qualité dans Hyperion

    Fonctionnalités :
    - Seuils adaptatifs basés sur l'historique
    - Détection d'anomalies de qualité
    - Alertes multi-niveaux (warning → error → critical)
    - Corrélation entre métriques de qualité
    - Recommandations automatiques d'amélioration
    """

    def __init__(self, alert_manager: AlertManager, thresholds: QualityThresholds | None = None):
        self.alert_manager = alert_manager
        self.thresholds = thresholds or QualityThresholds()

        # Historique pour seuils adaptatifs
        self.quality_history: dict[str, list] = {}

        # Setup des règles d'alerte par défaut
        self._setup_default_rules()

        logger.info("QualityAlerts initialisé avec seuils intelligents")

    def _setup_default_rules(self):
        """Configurer les règles d'alerte par défaut pour la qualité"""

        # === RAG QUALITY RULES ===

        # Taux d'hallucinations élevé
        self.alert_manager.add_rule(
            AlertRule(
                name="rag_high_hallucination_rate",
                query="hyperion_rag_hallucination_rate",
                threshold=self.thresholds.max_hallucination_rate,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.HALLUCINATION,
                duration=300,  # 5 minutes
                labels={"component": "rag", "type": "quality"},
                annotations={
                    "summary": "Taux d'hallucinations RAG élevé",
                    "description": "Le taux d'hallucinations détectées dépasse le seuil acceptable",
                    "runbook": "Vérifier la qualité des sources et ajuster les paramètres du modèle",
                },
            )
        )

        # Score de pertinence faible
        self.alert_manager.add_rule(
            AlertRule(
                name="rag_low_relevance_score",
                query="avg(hyperion_rag_response_quality_score)",
                threshold=self.thresholds.min_relevance_score,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.QUALITY,
                duration=600,  # 10 minutes
                labels={"component": "rag", "metric": "relevance"},
            )
        )

        # Temps de réponse RAG élevé
        self.alert_manager.add_rule(
            AlertRule(
                name="rag_high_response_time",
                query="histogram_quantile(0.95, hyperion_rag_processing_duration_seconds)",
                threshold=self.thresholds.max_rag_response_time,
                severity=AlertSeverity.ERROR,
                category=AlertCategory.LATENCY,
                duration=300,
                labels={"component": "rag", "metric": "latency"},
            )
        )

        # === ML QUALITY RULES ===

        # Précision du modèle faible
        self.alert_manager.add_rule(
            AlertRule(
                name="ml_low_accuracy",
                query="hyperion_ml_model_accuracy",
                threshold=self.thresholds.min_ml_accuracy,
                severity=AlertSeverity.ERROR,
                category=AlertCategory.ACCURACY,
                duration=900,  # 15 minutes
                labels={"component": "ml", "metric": "accuracy"},
            )
        )

        # Temps d'inférence ML élevé
        self.alert_manager.add_rule(
            AlertRule(
                name="ml_high_inference_time",
                query="histogram_quantile(0.90, hyperion_ml_feature_computation_seconds)",
                threshold=self.thresholds.max_ml_inference_time,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PERFORMANCE,
                duration=300,
                labels={"component": "ml", "metric": "inference_time"},
            )
        )

        # === API QUALITY RULES ===

        # Taux d'erreur API élevé
        self.alert_manager.add_rule(
            AlertRule(
                name="api_high_error_rate",
                query="rate(hyperion_api_requests_total{status=~'5..'}[5m])",
                threshold=self.thresholds.max_error_rate,
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.API,
                duration=60,
                labels={"component": "api", "metric": "error_rate"},
            )
        )

        # Latence API élevée
        self.alert_manager.add_rule(
            AlertRule(
                name="api_high_latency",
                query="histogram_quantile(0.95, hyperion_api_request_duration_seconds)",
                threshold=self.thresholds.max_api_response_time,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.LATENCY,
                duration=180,
                labels={"component": "api", "metric": "latency"},
            )
        )

    def check_quality_degradation(
        self, component: str, metric_name: str, current_value: float, **context
    ) -> str | None:
        """
        Vérifier la dégradation de qualité et déclencher des alertes si nécessaire
        Retourne l'ID de l'alerte si déclenchée
        """

        # Analyser la tendance
        trend = self._analyze_trend(component, metric_name, current_value)

        # Déterminer la sévérité basée sur l'écart aux seuils
        severity = self._calculate_severity(metric_name, current_value, trend)

        if severity == AlertSeverity.INFO:
            return None  # Pas d'alerte nécessaire

        # Générer l'alerte
        alert_id = self._fire_quality_alert(
            component=component,
            metric_name=metric_name,
            current_value=current_value,
            severity=severity,
            trend=trend,
            **context,
        )

        return alert_id

    def _analyze_trend(
        self, component: str, metric_name: str, current_value: float
    ) -> dict[str, Any]:
        """Analyser la tendance d'une métrique"""
        key = f"{component}.{metric_name}"

        if key not in self.quality_history:
            self.quality_history[key] = []

        history = self.quality_history[key]
        history.append(current_value)

        # Garder seulement les 100 dernières valeurs
        if len(history) > 100:
            history = history[-100:]
            self.quality_history[key] = history

        if len(history) < 5:
            return {"trend": "insufficient_data"}

        # Calcul de la tendance
        recent_avg = sum(history[-5:]) / 5
        older_avg = sum(history[-10:-5]) / 5 if len(history) >= 10 else recent_avg

        change_percent = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0

        return {
            "trend": (
                "improving"
                if change_percent > 5
                else "degrading" if change_percent < -5 else "stable"
            ),
            "change_percent": change_percent,
            "recent_avg": recent_avg,
            "historical_avg": sum(history) / len(history),
        }

    def _calculate_severity(self, metric_name: str, value: float, trend: dict) -> AlertSeverity:
        """Calculer la sévérité basée sur les seuils et la tendance"""

        # Mapping des métriques aux seuils
        threshold_mapping = {
            "relevance_score": ("min", self.thresholds.min_relevance_score),
            "coherence_score": ("min", self.thresholds.min_coherence_score),
            "hallucination_rate": ("max", self.thresholds.max_hallucination_rate),
            "confidence_score": ("min", self.thresholds.min_confidence_score),
            "response_time": ("max", self.thresholds.max_rag_response_time),
            "ml_accuracy": ("min", self.thresholds.min_ml_accuracy),
            "error_rate": ("max", self.thresholds.max_error_rate),
            "success_rate": ("min", self.thresholds.min_success_rate),
        }

        # Trouver le seuil approprié
        threshold_info = None
        for key, info in threshold_mapping.items():
            if key in metric_name.lower():
                threshold_info = info
                break

        if not threshold_info:
            return AlertSeverity.INFO

        threshold_type, threshold_value = threshold_info

        # Calculer l'écart au seuil
        if threshold_type == "min":
            deviation = (threshold_value - value) / threshold_value if threshold_value > 0 else 0
            exceeds_threshold = value < threshold_value
        else:  # max
            deviation = (value - threshold_value) / threshold_value if threshold_value > 0 else 0
            exceeds_threshold = value > threshold_value

        if not exceeds_threshold:
            return AlertSeverity.INFO

        # Déterminer sévérité basée sur l'écart et la tendance
        if deviation > 0.5:  # Écart > 50%
            severity = AlertSeverity.CRITICAL
        elif deviation > 0.3:  # Écart > 30%
            severity = AlertSeverity.ERROR
        elif deviation > 0.1:  # Écart > 10%
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.INFO

        # Ajustement selon la tendance
        if trend.get("trend") == "degrading" and trend.get("change_percent", 0) < -15:
            # Dégradation rapide, augmenter la sévérité
            if severity == AlertSeverity.WARNING:
                severity = AlertSeverity.ERROR
            elif severity == AlertSeverity.ERROR:
                severity = AlertSeverity.CRITICAL

        return severity

    def _fire_quality_alert(
        self,
        component: str,
        metric_name: str,
        current_value: float,
        severity: AlertSeverity,
        trend: dict,
        **context,
    ) -> str:
        """Déclencher une alerte de qualité"""

        # Déterminer la catégorie
        category = self._get_alert_category(metric_name)

        # Générer titre et message
        title = f"Quality Issue: {component.upper()} {metric_name}"

        message_parts = [
            f"Metric: {metric_name} = {current_value:.3f}",
            f"Component: {component}",
            f"Trend: {trend.get('trend', 'unknown')}",
        ]

        if trend.get("change_percent"):
            message_parts.append(f"Change: {trend['change_percent']:.1f}%")

        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            message_parts.append(f"Context: {context_str}")

        message = "\n".join(message_parts)

        # Ajouter des recommandations
        recommendations = self._get_recommendations(metric_name, current_value, trend)
        if recommendations:
            message += f"\n\nRecommendations:\n{recommendations}"

        # Déclencher l'alerte
        return self.alert_manager.fire_alert(
            title=title,
            message=message,
            severity=severity,
            category=category,
            source=f"{component}:quality_monitor",
            labels={
                "component": component,
                "metric": metric_name,
                "quality_type": category.name.lower(),
            },
            annotations={
                "current_value": current_value,
                "trend": trend.get("trend"),
                "change_percent": trend.get("change_percent", 0),
                **context,
            },
        )

    def _get_alert_category(self, metric_name: str) -> AlertCategory:
        """Déterminer la catégorie d'alerte selon la métrique"""
        metric_lower = metric_name.lower()

        if "hallucination" in metric_lower:
            return AlertCategory.HALLUCINATION
        elif any(x in metric_lower for x in ["accuracy", "precision", "recall"]):
            return AlertCategory.ACCURACY
        elif any(x in metric_lower for x in ["time", "latency", "duration"]):
            return AlertCategory.LATENCY
        elif "error" in metric_lower:
            return AlertCategory.API
        elif any(x in metric_lower for x in ["relevance", "coherence", "confidence"]):
            return AlertCategory.QUALITY
        else:
            return AlertCategory.PERFORMANCE

    def _get_recommendations(self, metric_name: str, value: float, trend: dict) -> str:
        """Générer des recommandations d'amélioration"""
        recommendations = []
        metric_lower = metric_name.lower()

        # Recommandations spécifiques par métrique
        if "hallucination" in metric_lower and value > self.thresholds.max_hallucination_rate:
            recommendations.extend(
                [
                    "• Vérifier la qualité et fraîcheur des sources de données",
                    "• Ajuster les paramètres de température du modèle",
                    "• Améliorer les prompts de génération",
                    "• Renforcer la validation des réponses",
                ]
            )

        elif "relevance" in metric_lower and value < self.thresholds.min_relevance_score:
            recommendations.extend(
                [
                    "• Optimiser l'algorithme de recherche sémantique",
                    "• Revoir l'indexation des documents",
                    "• Ajuster les embeddings utilisés",
                    "• Améliorer le preprocessing des requêtes",
                ]
            )

        elif "response_time" in metric_lower or "latency" in metric_lower:
            recommendations.extend(
                [
                    "• Optimiser les requêtes base de données",
                    "• Mettre en place du cache pour les requêtes fréquentes",
                    "• Paralléliser le traitement quand possible",
                    "• Vérifier les ressources système (CPU/mémoire)",
                ]
            )

        elif "accuracy" in metric_lower and value < self.thresholds.min_ml_accuracy:
            recommendations.extend(
                [
                    "• Enrichir les données d'entraînement",
                    "• Ajuster l'hyperparamétrage du modèle",
                    "• Vérifier la qualité des features",
                    "• Considérer un réentraînement",
                ]
            )

        elif "error_rate" in metric_lower:
            recommendations.extend(
                [
                    "• Analyser les logs d'erreur récents",
                    "• Vérifier la santé des services dépendants",
                    "• Améliorer la gestion d'erreur",
                    "• Monitorer les ressources système",
                ]
            )

        # Recommandations basées sur la tendance
        if trend.get("trend") == "degrading":
            recommendations.extend(
                [
                    "• Analyser les changements récents (code, config, données)",
                    "• Comparer avec les performances historiques",
                    "• Vérifier l'impact des montées de charge",
                ]
            )

        return (
            "\n".join(recommendations)
            if recommendations
            else "Analyser les métriques connexes pour identifier la cause"
        )

    def update_thresholds(self, **kwargs):
        """Mettre à jour les seuils dynamiquement"""
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
                logger.info(f"Seuil mis à jour: {key} = {value}")

    def get_quality_summary(self) -> dict[str, Any]:
        """Obtenir un résumé de l'état qualité"""
        # Obtenir les alertes qualité actives
        quality_alerts = [
            alert
            for alert in self.alert_manager.get_active_alerts()
            if alert.category
            in [AlertCategory.QUALITY, AlertCategory.HALLUCINATION, AlertCategory.ACCURACY]
        ]

        return {
            "active_quality_alerts": len(quality_alerts),
            "quality_alerts_by_severity": {
                severity.name: len([a for a in quality_alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "thresholds": {
                "min_relevance_score": self.thresholds.min_relevance_score,
                "max_hallucination_rate": self.thresholds.max_hallucination_rate,
                "min_ml_accuracy": self.thresholds.min_ml_accuracy,
                "max_error_rate": self.thresholds.max_error_rate,
            },
            "trending_metrics": len(self.quality_history),
        }

    def export_quality_config(self) -> dict[str, Any]:
        """Exporter la configuration qualité"""
        return {
            "thresholds": {
                attr: getattr(self.thresholds, attr)
                for attr in dir(self.thresholds)
                if not attr.startswith("_")
            },
            "quality_history_keys": list(self.quality_history.keys()),
            "rules_count": len(
                [
                    rule
                    for rule in self.alert_manager.alert_rules.values()
                    if rule.category
                    in [AlertCategory.QUALITY, AlertCategory.HALLUCINATION, AlertCategory.ACCURACY]
                ]
            ),
        }
