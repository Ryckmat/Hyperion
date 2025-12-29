"""
Intelligence Engine for Hyperion v2.9

Moteur d'intelligence central pour analytics et insights automatisés.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsEvent:
    """Événement pour analytics"""

    timestamp: float
    event_type: str
    source: str
    data: dict[str, Any]
    user_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Insight:
    """Insight généré par l'intelligence"""

    id: str
    title: str
    description: str
    confidence: float
    category: str
    impact_level: str  # low, medium, high, critical

    # Données supportant l'insight
    evidence: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    # Métadonnées
    generated_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class AnalyticsSummary:
    """Résumé d'analytics pour une période"""

    period_start: datetime
    period_end: datetime
    total_events: int
    unique_users: int
    top_events: list[tuple[str, int]]
    insights_generated: int
    key_trends: list[str]
    performance_metrics: dict[str, float]


class IntelligenceEngine:
    """
    Moteur d'intelligence central pour Hyperion v2.9

    Fonctionnalités :
    - Collecte et agrégation d'événements multi-sources
    - Détection de patterns en temps réel
    - Génération d'insights automatiques
    - Prédictions comportementales
    - Recommandations intelligentes
    - Analytics de performance et usage
    - Dashboard intelligent en temps réel
    """

    def __init__(
        self,
        max_events: int = 100000,
        insight_generation_interval: int = 300,  # 5 minutes
        enable_real_time_analysis: bool = True,
    ):

        self.max_events = max_events
        self.insight_generation_interval = insight_generation_interval
        self.enable_real_time_analysis = enable_real_time_analysis

        # Storage des événements
        self.event_buffer: deque = deque(maxlen=max_events)
        self.event_index: dict[str, list[AnalyticsEvent]] = defaultdict(list)

        # Insights générés
        self.active_insights: dict[str, Insight] = {}
        self.insight_history: list[Insight] = []

        # Patterns détectés
        self.detected_patterns: dict[str, Any] = {}
        self.pattern_confidence_threshold = 0.7

        # Analytics en temps réel
        self.real_time_stats = {
            "events_per_minute": deque(maxlen=60),
            "active_users": set(),
            "current_trends": [],
            "anomalies_detected": 0,
        }

        # Configuration des règles d'insights
        self.insight_rules = {
            "performance_degradation": {
                "threshold": 0.3,  # 30% de dégradation
                "window_minutes": 15,
                "enabled": True,
            },
            "usage_spike": {
                "multiplier": 2.0,  # 2x l'usage normal
                "window_minutes": 10,
                "enabled": True,
            },
            "error_pattern": {
                "threshold": 0.1,  # 10% d'erreurs
                "window_minutes": 5,
                "enabled": True,
            },
            "user_behavior_change": {
                "deviation_threshold": 0.4,
                "window_hours": 24,
                "enabled": True,
            },
        }

        # Callbacks pour événements
        self.event_callbacks: list[Callable] = []
        self.insight_callbacks: list[Callable] = []

        # Threading pour analyses
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._analysis_running = False

        logger.info("IntelligenceEngine initialisé")

    def start_real_time_analysis(self):
        """Démarrer l'analyse en temps réel"""
        if not self.enable_real_time_analysis or self._analysis_running:
            return

        self._analysis_running = True

        # Lancer la boucle d'analyse en arrière-plan
        asyncio.create_task(self._analysis_loop())

        logger.info("Analyse temps réel démarrée")

    def stop_real_time_analysis(self):
        """Arrêter l'analyse en temps réel"""
        self._analysis_running = False
        logger.info("Analyse temps réel arrêtée")

    async def _analysis_loop(self):
        """Boucle principale d'analyse"""
        while self._analysis_running:
            try:
                # Analyse des patterns
                await self._detect_patterns()

                # Génération d'insights
                await self._generate_insights()

                # Mise à jour des stats temps réel
                self._update_real_time_stats()

                # Nettoyage des anciens insights
                self._cleanup_expired_insights()

                # Attendre avant prochaine itération
                await asyncio.sleep(self.insight_generation_interval)

            except Exception as e:
                logger.error(f"Erreur boucle d'analyse: {e}")
                await asyncio.sleep(10)

    def record_event(self, event: AnalyticsEvent):
        """Enregistrer un événement pour analyse"""

        # Ajouter au buffer principal
        self.event_buffer.append(event)

        # Indexer par type et source
        self.event_index[event.event_type].append(event)
        self.event_index[f"source:{event.source}"].append(event)

        if event.user_id:
            self.event_index[f"user:{event.user_id}"].append(event)
            self.real_time_stats["active_users"].add(event.user_id)

        # Nettoyage des index si nécessaire
        self._cleanup_event_indexes()

        # Callbacks immédiats
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Erreur callback événement: {e}")

        # Analyse immédiate si activée
        if self.enable_real_time_analysis:
            asyncio.create_task(self._analyze_immediate_patterns(event))

    async def _analyze_immediate_patterns(self, event: AnalyticsEvent):
        """Analyse immédiate de patterns critiques"""

        # Détection d'anomalies critiques
        if event.event_type == "error":
            await self._check_error_spike(event)
        elif event.event_type == "performance":
            await self._check_performance_degradation(event)
        elif event.event_type == "user_action":
            await self._check_unusual_behavior(event)

    async def _detect_patterns(self):
        """Détection de patterns dans les événements"""

        if not self.event_buffer:
            return

        # Analyze temporal patterns in events
        await self._detect_temporal_patterns()

        # Patterns d'usage
        await self._detect_usage_patterns()

        # Patterns de performance
        await self._detect_performance_patterns()

        # Patterns comportementaux
        await self._detect_behavioral_patterns()

    async def _detect_temporal_patterns(self):
        """Détection de patterns temporels"""

        # Analyser les événements par heure
        hourly_counts = defaultdict(int)

        current_time = time.time()
        day_ago = current_time - (24 * 3600)

        for event in self.event_buffer:
            if event.timestamp > day_ago:
                hour = int((event.timestamp % (24 * 3600)) // 3600)
                hourly_counts[hour] += 1

        if hourly_counts:
            # Détecter pics d'activité
            avg_hourly = np.mean(list(hourly_counts.values()))
            std_hourly = np.std(list(hourly_counts.values()))

            peak_hours = []
            for hour, count in hourly_counts.items():
                if count > avg_hourly + (2 * std_hourly):
                    peak_hours.append(hour)

            if peak_hours:
                self.detected_patterns["peak_hours"] = {
                    "hours": peak_hours,
                    "confidence": 0.8,
                    "detected_at": current_time,
                }

    async def _detect_usage_patterns(self):
        """Détection de patterns d'usage"""

        # Analyser les événements utilisateur
        user_activities = defaultdict(list)

        current_time = time.time()
        week_ago = current_time - (7 * 24 * 3600)

        for event in self.event_buffer:
            if event.user_id and event.timestamp > week_ago:
                user_activities[event.user_id].append(event)

        # Détecter utilisateurs super-actifs
        activity_counts = {user: len(events) for user, events in user_activities.items()}

        if activity_counts:
            avg_activity = np.mean(list(activity_counts.values()))
            std_activity = np.std(list(activity_counts.values()))

            super_users = []
            for user, count in activity_counts.items():
                if count > avg_activity + (3 * std_activity):
                    super_users.append(user)

            if super_users:
                self.detected_patterns["super_users"] = {
                    "users": super_users,
                    "threshold": avg_activity + (3 * std_activity),
                    "confidence": 0.9,
                    "detected_at": current_time,
                }

    async def _detect_performance_patterns(self):
        """Détection de patterns de performance"""

        # Analyser événements de performance
        performance_events = [
            e
            for e in self.event_buffer
            if e.event_type in ["api_request", "rag_query", "ml_prediction"]
        ]

        if len(performance_events) < 50:
            return

        # Analyser les temps de réponse
        recent_events = [
            e for e in performance_events if e.timestamp > time.time() - 3600  # Dernière heure
        ]

        response_times = []
        for event in recent_events:
            if "response_time" in event.data:
                response_times.append(event.data["response_time"])

        if response_times:
            avg_time = np.mean(response_times)
            p95_time = np.percentile(response_times, 95)

            # Détecter dégradation
            if p95_time > avg_time * 2:
                self.detected_patterns["performance_degradation"] = {
                    "avg_response_time": avg_time,
                    "p95_response_time": p95_time,
                    "degradation_factor": p95_time / avg_time,
                    "confidence": 0.85,
                    "detected_at": time.time(),
                }

    async def _detect_behavioral_patterns(self):
        """Détection de patterns comportementaux"""

        # Analyser séquences d'actions utilisateur
        user_sequences = defaultdict(list)

        for event in self.event_buffer:
            if event.user_id and event.event_type == "user_action":
                action = event.data.get("action", "unknown")
                user_sequences[event.user_id].append(action)

        # Détecter patterns de navigation communs
        common_sequences = defaultdict(int)

        for user_actions in user_sequences.values():
            for i in range(len(user_actions) - 2):
                sequence = tuple(user_actions[i : i + 3])
                common_sequences[sequence] += 1

        # Garder les séquences les plus fréquentes
        if common_sequences:
            sorted_sequences = sorted(common_sequences.items(), key=lambda x: x[1], reverse=True)

            top_sequences = sorted_sequences[:5]

            self.detected_patterns["common_workflows"] = {
                "sequences": top_sequences,
                "total_users_analyzed": len(user_sequences),
                "confidence": 0.7,
                "detected_at": time.time(),
            }

    async def _generate_insights(self):
        """Génération d'insights basés sur les patterns"""

        generated_insights = []

        # Insights de performance
        if "performance_degradation" in self.detected_patterns:
            insight = await self._generate_performance_insight()
            if insight:
                generated_insights.append(insight)

        # Insights d'usage
        if "super_users" in self.detected_patterns:
            insight = await self._generate_usage_insight()
            if insight:
                generated_insights.append(insight)

        # Insights temporels
        if "peak_hours" in self.detected_patterns:
            insight = await self._generate_temporal_insight()
            if insight:
                generated_insights.append(insight)

        # Insights comportementaux
        if "common_workflows" in self.detected_patterns:
            insight = await self._generate_behavioral_insight()
            if insight:
                generated_insights.append(insight)

        # Ajouter les nouveaux insights
        for insight in generated_insights:
            self.active_insights[insight.id] = insight
            self.insight_history.append(insight)

            # Callbacks
            for callback in self.insight_callbacks:
                try:
                    callback(insight)
                except Exception as e:
                    logger.error(f"Erreur callback insight: {e}")

    async def _generate_performance_insight(self) -> Insight | None:
        """Générer insight de performance"""

        pattern = self.detected_patterns["performance_degradation"]
        degradation = pattern["degradation_factor"]

        if degradation < 1.5:
            return None

        impact = "critical" if degradation > 3 else "high" if degradation > 2 else "medium"

        insight = Insight(
            id=f"perf_degradation_{int(time.time())}",
            title="Dégradation de performance détectée",
            description=f"Les temps de réponse P95 sont {degradation:.1f}x plus élevés que la moyenne.",
            confidence=pattern["confidence"],
            category="performance",
            impact_level=impact,
            evidence={
                "avg_response_time": pattern["avg_response_time"],
                "p95_response_time": pattern["p95_response_time"],
                "degradation_factor": degradation,
            },
            recommendations=[
                "Analyser les requêtes les plus lentes",
                "Vérifier la charge système actuelle",
                "Optimiser les requêtes base de données",
                "Considérer l'ajout de cache",
            ],
            tags=["performance", "latency", "optimization"],
            expires_at=time.time() + 3600,  # Expire dans 1h
        )

        return insight

    async def _generate_usage_insight(self) -> Insight | None:
        """Générer insight d'usage"""

        pattern = self.detected_patterns["super_users"]
        super_users = pattern["users"]

        insight = Insight(
            id=f"super_users_{int(time.time())}",
            title=f"{len(super_users)} utilisateurs super-actifs détectés",
            description=f"Ces utilisateurs ont une activité {pattern['threshold']:.0f}% supérieure à la moyenne.",
            confidence=pattern["confidence"],
            category="usage",
            impact_level="medium",
            evidence={
                "super_users_count": len(super_users),
                "activity_threshold": pattern["threshold"],
            },
            recommendations=[
                "Analyser les besoins de ces utilisateurs actifs",
                "Optimiser les fonctionnalités qu'ils utilisent le plus",
                "Considérer un programme de feedback utilisateur",
                "Prévoir une montée en charge",
            ],
            tags=["usage", "users", "engagement"],
            expires_at=time.time() + (24 * 3600),  # Expire dans 24h
        )

        return insight

    async def _generate_temporal_insight(self) -> Insight | None:
        """Générer insight temporel"""

        pattern = self.detected_patterns["peak_hours"]
        peak_hours = pattern["hours"]

        insight = Insight(
            id=f"peak_hours_{int(time.time())}",
            title="Pics d'activité identifiés",
            description=f"Activité concentrée sur {len(peak_hours)} heures: {', '.join(map(str, peak_hours))}h",
            confidence=pattern["confidence"],
            category="temporal",
            impact_level="low",
            evidence={"peak_hours": peak_hours, "pattern_strength": pattern["confidence"]},
            recommendations=[
                "Optimiser les ressources pour ces créneaux",
                "Planifier la maintenance en dehors des pics",
                "Analyser les causes de ces pics d'activité",
                "Ajuster la capacité selon les horaires",
            ],
            tags=["temporal", "capacity", "planning"],
            expires_at=time.time() + (7 * 24 * 3600),  # Expire dans 7j
        )

        return insight

    async def _generate_behavioral_insight(self) -> Insight | None:
        """Générer insight comportemental"""

        pattern = self.detected_patterns["common_workflows"]
        top_sequences = pattern["sequences"]

        if not top_sequences:
            return None

        most_common = top_sequences[0]
        sequence, count = most_common

        insight = Insight(
            id=f"workflow_{int(time.time())}",
            title="Workflow utilisateur principal identifié",
            description=f"Séquence la plus fréquente: {' → '.join(sequence)} ({count} occurrences)",
            confidence=pattern["confidence"],
            category="behavior",
            impact_level="low",
            evidence={
                "top_sequence": sequence,
                "occurrence_count": count,
                "total_sequences": len(top_sequences),
            },
            recommendations=[
                "Optimiser ce workflow principal",
                "Créer des raccourcis pour cette séquence",
                "Analyser les points de friction",
                "Documenter les meilleures pratiques",
            ],
            tags=["behavior", "workflow", "ux"],
            expires_at=time.time() + (7 * 24 * 3600),  # Expire dans 7j
        )

        return insight

    # Méthodes de vérification temps réel

    async def _check_error_spike(self, _event: AnalyticsEvent):
        """Vérifier les pics d'erreur"""

        recent_events = [
            e
            for e in self.event_buffer
            if e.timestamp > time.time() - 300 and e.event_type == "error"
        ]

        error_rate = len(recent_events) / max(
            len([e for e in self.event_buffer if e.timestamp > time.time() - 300]), 1
        )

        if error_rate > self.insight_rules["error_pattern"]["threshold"]:
            insight = Insight(
                id=f"error_spike_{int(time.time())}",
                title="Pic d'erreurs détecté",
                description=f"Taux d'erreur de {error_rate:.1%} sur les 5 dernières minutes",
                confidence=0.9,
                category="reliability",
                impact_level="critical",
                evidence={"error_rate": error_rate, "recent_errors": len(recent_events)},
                recommendations=[
                    "Investiguer immédiatement les erreurs",
                    "Vérifier l'état des services critiques",
                    "Analyser les logs d'erreur récents",
                ],
                tags=["error", "reliability", "critical"],
            )

            self.active_insights[insight.id] = insight

    async def _check_performance_degradation(self, event: AnalyticsEvent):
        """Vérifier la dégradation de performance"""

        if "response_time" not in event.data:
            return

        recent_times = [
            e.data.get("response_time", 0)
            for e in self.event_buffer
            if (
                e.timestamp > time.time() - 900  # 15 min
                and e.event_type == event.event_type
                and "response_time" in e.data
            )
        ]

        if len(recent_times) < 10:
            return

        avg_time = np.mean(recent_times[-10:])  # 10 derniers
        baseline_time = np.mean(recent_times[:-10]) if len(recent_times) > 20 else avg_time

        if avg_time > baseline_time * 1.5:  # 50% plus lent
            insight = Insight(
                id=f"perf_degrade_{int(time.time())}",
                title="Performance en dégradation",
                description=f"Temps de réponse {event.event_type} augmenté de {(avg_time/baseline_time-1)*100:.1f}%",
                confidence=0.8,
                category="performance",
                impact_level="high",
                evidence={
                    "current_avg": avg_time,
                    "baseline_avg": baseline_time,
                    "degradation_percent": (avg_time / baseline_time - 1) * 100,
                },
                recommendations=[
                    "Analyser les goulots d'étranglement",
                    "Vérifier les ressources système",
                    "Optimiser les requêtes lentes",
                ],
                tags=["performance", "degradation"],
            )

            self.active_insights[insight.id] = insight

    async def _check_unusual_behavior(self, event: AnalyticsEvent):
        """Vérifier les comportements inhabituels"""

        if not event.user_id:
            return

        user_events = [
            e
            for e in self.event_buffer
            if e.user_id == event.user_id and e.timestamp > time.time() - 3600
        ]

        # Détecter activité anormalement élevée
        if len(user_events) > 100:  # Plus de 100 actions/heure
            insight = Insight(
                id=f"unusual_activity_{event.user_id}_{int(time.time())}",
                title="Activité utilisateur inhabituelle",
                description=f"Utilisateur {event.user_id}: {len(user_events)} actions en 1h",
                confidence=0.7,
                category="security",
                impact_level="medium",
                evidence={
                    "user_id": event.user_id,
                    "actions_count": len(user_events),
                    "time_window": "1h",
                },
                recommendations=[
                    "Vérifier si c'est un comportement légitime",
                    "Analyser le type d'actions effectuées",
                    "Considérer un rate limiting",
                ],
                tags=["security", "behavior", "unusual"],
            )

            self.active_insights[insight.id] = insight

    def _update_real_time_stats(self):
        """Mise à jour des statistiques temps réel"""

        current_time = time.time()
        minute_ago = current_time - 60

        # Compter événements de la dernière minute
        recent_events = [e for e in self.event_buffer if e.timestamp > minute_ago]

        self.real_time_stats["events_per_minute"].append(len(recent_events))

        # Nettoyer les utilisateurs actifs (dernières 30 minutes)
        active_threshold = current_time - (30 * 60)
        active_users = set()

        for event in self.event_buffer:
            if event.user_id and event.timestamp > active_threshold:
                active_users.add(event.user_id)

        self.real_time_stats["active_users"] = active_users

        # Détecter tendances
        if len(self.real_time_stats["events_per_minute"]) >= 5:
            recent_avg = np.mean(list(self.real_time_stats["events_per_minute"])[-5:])
            older_avg = np.mean(list(self.real_time_stats["events_per_minute"])[:-5])

            if recent_avg > older_avg * 1.5:
                self.real_time_stats["current_trends"] = ["increasing_activity"]
            elif recent_avg < older_avg * 0.5:
                self.real_time_stats["current_trends"] = ["decreasing_activity"]
            else:
                self.real_time_stats["current_trends"] = ["stable_activity"]

    def _cleanup_expired_insights(self):
        """Nettoyer les insights expirés"""

        current_time = time.time()
        expired_insights = []

        for insight_id, insight in self.active_insights.items():
            if insight.expires_at and insight.expires_at < current_time:
                expired_insights.append(insight_id)

        for insight_id in expired_insights:
            del self.active_insights[insight_id]

        # Garder seulement les 1000 derniers insights dans l'historique
        if len(self.insight_history) > 1000:
            self.insight_history = self.insight_history[-1000:]

    def _cleanup_event_indexes(self):
        """Nettoyer les index d'événements"""

        max_per_index = 10000

        for key, events in self.event_index.items():
            if len(events) > max_per_index:
                # Garder les plus récents
                self.event_index[key] = sorted(events, key=lambda x: x.timestamp)[-max_per_index:]

    # API publique

    def get_current_insights(
        self, category: str | None = None, impact_level: str | None = None
    ) -> list[Insight]:
        """Obtenir les insights actuels"""

        insights = list(self.active_insights.values())

        if category:
            insights = [i for i in insights if i.category == category]

        if impact_level:
            insights = [i for i in insights if i.impact_level == impact_level]

        return sorted(insights, key=lambda x: x.confidence, reverse=True)

    def get_analytics_summary(self, hours: int = 24) -> AnalyticsSummary:
        """Obtenir un résumé d'analytics"""

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        cutoff_timestamp = start_time.timestamp()

        # Filtrer événements de la période
        period_events = [e for e in self.event_buffer if e.timestamp > cutoff_timestamp]

        # Statistiques de base
        total_events = len(period_events)
        unique_users = len({e.user_id for e in period_events if e.user_id})

        # Top événements
        event_counts = defaultdict(int)
        for event in period_events:
            event_counts[event.event_type] += 1

        top_events = sorted(event_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Insights générés
        period_insights = [i for i in self.insight_history if i.generated_at > cutoff_timestamp]

        # Tendances clés
        key_trends = list(self.real_time_stats["current_trends"])

        # Métriques de performance
        performance_events = [e for e in period_events if "response_time" in e.data]

        performance_metrics = {}
        if performance_events:
            response_times = [e.data["response_time"] for e in performance_events]
            performance_metrics = {
                "avg_response_time": np.mean(response_times),
                "p95_response_time": np.percentile(response_times, 95),
                "total_requests": len(performance_events),
            }

        return AnalyticsSummary(
            period_start=start_time,
            period_end=end_time,
            total_events=total_events,
            unique_users=unique_users,
            top_events=top_events,
            insights_generated=len(period_insights),
            key_trends=key_trends,
            performance_metrics=performance_metrics,
        )

    def get_real_time_dashboard_data(self) -> dict[str, Any]:
        """Données pour dashboard temps réel"""

        return {
            "current_timestamp": time.time(),
            "active_users_count": len(self.real_time_stats["active_users"]),
            "events_last_minute": (
                list(self.real_time_stats["events_per_minute"])[-1]
                if self.real_time_stats["events_per_minute"]
                else 0
            ),
            "events_trend": list(self.real_time_stats["events_per_minute"]),
            "current_trends": self.real_time_stats["current_trends"],
            "active_insights_count": len(self.active_insights),
            "critical_insights": len(
                [i for i in self.active_insights.values() if i.impact_level == "critical"]
            ),
            "anomalies_detected": self.real_time_stats["anomalies_detected"],
            "top_patterns": list(self.detected_patterns.keys()),
        }

    def add_event_callback(self, callback: Callable[[AnalyticsEvent], None]):
        """Ajouter callback pour événements"""
        self.event_callbacks.append(callback)

    def add_insight_callback(self, callback: Callable[[Insight], None]):
        """Ajouter callback pour insights"""
        self.insight_callbacks.append(callback)

    def export_analytics_data(self, format: str = "json") -> str:
        """Exporter données d'analytics"""

        data = {
            "export_timestamp": time.time(),
            "total_events": len(self.event_buffer),
            "active_insights": [
                {
                    "id": i.id,
                    "title": i.title,
                    "category": i.category,
                    "impact_level": i.impact_level,
                    "confidence": i.confidence,
                }
                for i in self.active_insights.values()
            ],
            "detected_patterns": dict(self.detected_patterns),
            "real_time_stats": {
                "active_users_count": len(self.real_time_stats["active_users"]),
                "current_trends": self.real_time_stats["current_trends"],
                "events_per_minute_avg": (
                    np.mean(list(self.real_time_stats["events_per_minute"]))
                    if self.real_time_stats["events_per_minute"]
                    else 0
                ),
            },
        }

        if format == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            raise ValueError(f"Format non supporté: {format}")


# Helper functions
def create_event(
    event_type: str, source: str, data: dict[str, Any], user_id: str | None = None, **kwargs
) -> AnalyticsEvent:
    """Créer un événement d'analytics"""
    return AnalyticsEvent(
        timestamp=time.time(),
        event_type=event_type,
        source=source,
        data=data,
        user_id=user_id,
        **kwargs,
    )


# Instance globale
intelligence_engine = IntelligenceEngine()


def record_analytics_event(
    event_type: str, source: str, data: dict[str, Any], user_id: str | None = None, **kwargs
):
    """Enregistrer un événement d'analytics"""
    event = create_event(event_type, source, data, user_id, **kwargs)
    intelligence_engine.record_event(event)
