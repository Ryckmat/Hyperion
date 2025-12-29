"""
Prometheus Metrics Exporter for Hyperion v3.0

Expose des métriques enterprise-grade pour supervision et alerting.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        REGISTRY,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        start_http_server,
    )
except ImportError:
    logger.warning("prometheus_client non disponible - mode fallback activé")
    from .prometheus_fallback import (
        REGISTRY,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        start_http_server,
    )


@dataclass
class MetricConfig:
    """Configuration pour métriques Prometheus"""

    port: int = 8090
    enable_default_metrics: bool = True
    custom_labels: dict[str, str] = None


class PrometheusExporter:
    """
    Exportateur de métriques Prometheus pour Hyperion

    Expose toutes les métriques clés pour monitoring enterprise :
    - Performance API (latence, throughput, erreurs)
    - Santé des modules (RAG, ML, Neo4j, Qdrant)
    - Utilisation ressources (CPU, mémoire, GPU)
    - Métriques business (profils analysés, qualité RAG)
    """

    def __init__(self, config: MetricConfig | None = None):
        self.config = config or MetricConfig()
        self.registry = CollectorRegistry() if not self.config.enable_default_metrics else REGISTRY
        self._initialize_metrics()
        self._server_started = False

        logger.info(f"PrometheusExporter initialisé - Port: {self.config.port}")

    def _initialize_metrics(self):
        """Initialiser toutes les métriques Hyperion"""

        # === API METRICS ===
        self.api_requests_total = Counter(
            "hyperion_api_requests_total",
            "Total API requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.api_request_duration = Histogram(
            "hyperion_api_request_duration_seconds",
            "API request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry,
        )

        self.api_active_connections = Gauge(
            "hyperion_api_active_connections",
            "Number of active API connections",
            registry=self.registry,
        )

        # === RAG METRICS ===
        self.rag_queries_total = Counter(
            "hyperion_rag_queries_total",
            "Total RAG queries",
            ["repo", "status"],
            registry=self.registry,
        )

        self.rag_response_quality = Histogram(
            "hyperion_rag_response_quality_score",
            "RAG response quality score (0-1)",
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry,
        )

        self.rag_processing_time = Histogram(
            "hyperion_rag_processing_duration_seconds",
            "RAG query processing time",
            ["stage"],  # embedding, search, generation, validation
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry,
        )

        self.rag_hallucination_rate = Gauge(
            "hyperion_rag_hallucination_rate",
            "Current hallucination detection rate",
            registry=self.registry,
        )

        # === ML METRICS ===
        self.ml_model_predictions = Counter(
            "hyperion_ml_predictions_total",
            "Total ML model predictions",
            ["model_name", "model_version", "status"],
            registry=self.registry,
        )

        self.ml_model_accuracy = Gauge(
            "hyperion_ml_model_accuracy",
            "Current model accuracy",
            ["model_name", "model_version"],
            registry=self.registry,
        )

        self.ml_feature_computation_time = Histogram(
            "hyperion_ml_feature_computation_seconds",
            "Time to compute ML features",
            ["feature_set"],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry,
        )

        # === DATABASE METRICS ===
        self.db_connections = Gauge(
            "hyperion_db_connections",
            "Number of database connections",
            ["database"],  # neo4j, qdrant, sqlite
            registry=self.registry,
        )

        self.db_query_duration = Histogram(
            "hyperion_db_query_duration_seconds",
            "Database query duration",
            ["database", "operation"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry,
        )

        self.qdrant_vector_count = Gauge(
            "hyperion_qdrant_vectors_total",
            "Total vectors in Qdrant collections",
            ["collection"],
            registry=self.registry,
        )

        # === SYSTEM METRICS ===
        self.system_info = Info(
            "hyperion_system_info", "System information", registry=self.registry
        )

        self.memory_usage = Gauge(
            "hyperion_memory_usage_bytes",
            "Memory usage in bytes",
            ["component"],  # total, api, ml, rag
            registry=self.registry,
        )

        self.cpu_usage = Gauge(
            "hyperion_cpu_usage_percent",
            "CPU usage percentage",
            ["component"],
            registry=self.registry,
        )

        # === BUSINESS METRICS ===
        self.profiles_analyzed = Counter(
            "hyperion_profiles_analyzed_total",
            "Total repositories analyzed",
            ["status"],  # success, failure
            registry=self.registry,
        )

        self.active_users = Gauge(
            "hyperion_active_users",
            "Number of active users",
            ["timeframe"],  # 5m, 1h, 24h
            registry=self.registry,
        )

        logger.debug("Toutes les métriques Prometheus initialisées")

    def start_server(self) -> None:
        """Démarrer le serveur de métriques Prometheus"""
        if not self._server_started:
            start_http_server(self.config.port, registry=self.registry)
            self._server_started = True
            logger.info(f"Serveur Prometheus démarré sur port {self.config.port}")

            # Initialiser les métriques système
            self._update_system_info()

    def _update_system_info(self):
        """Mettre à jour les informations système"""
        import platform

        from hyperion import __version__

        self.system_info.info(
            {
                "version": __version__,
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "architecture": platform.architecture()[0],
            }
        )

    # === API METRICS HELPERS ===

    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """Enregistrer une requête API"""
        self.api_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()

        self.api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def update_active_connections(self, count: int):
        """Mettre à jour le nombre de connexions actives"""
        self.api_active_connections.set(count)

    # === RAG METRICS HELPERS ===

    def record_rag_query(
        self, repo: str, status: str, quality_score: float, processing_times: dict[str, float]
    ):
        """Enregistrer une requête RAG complète"""
        self.rag_queries_total.labels(repo=repo, status=status).inc()
        self.rag_response_quality.observe(quality_score)

        for stage, duration in processing_times.items():
            self.rag_processing_time.labels(stage=stage).observe(duration)

    def update_hallucination_rate(self, rate: float):
        """Mettre à jour le taux d'hallucinations détectées"""
        self.rag_hallucination_rate.set(rate)

    # === ML METRICS HELPERS ===

    def record_ml_prediction(
        self, model_name: str, model_version: str, status: str, accuracy: float | None = None
    ):
        """Enregistrer une prédiction ML"""
        self.ml_model_predictions.labels(
            model_name=model_name, model_version=model_version, status=status
        ).inc()

        if accuracy is not None:
            self.ml_model_accuracy.labels(model_name=model_name, model_version=model_version).set(
                accuracy
            )

    def record_feature_computation(self, feature_set: str, duration: float):
        """Enregistrer le temps de calcul des features"""
        self.ml_feature_computation_time.labels(feature_set=feature_set).observe(duration)

    # === DATABASE METRICS HELPERS ===

    def record_db_query(self, database: str, operation: str, duration: float):
        """Enregistrer une requête base de données"""
        self.db_query_duration.labels(database=database, operation=operation).observe(duration)

    def update_db_connections(self, database: str, count: int):
        """Mettre à jour le nombre de connexions DB"""
        self.db_connections.labels(database=database).set(count)

    def update_qdrant_vectors(self, collection: str, count: int):
        """Mettre à jour le nombre de vecteurs Qdrant"""
        self.qdrant_vector_count.labels(collection=collection).set(count)

    # === SYSTEM METRICS HELPERS ===

    def update_resource_usage(self, component: str, memory_bytes: int, cpu_percent: float):
        """Mettre à jour l'utilisation des ressources"""
        self.memory_usage.labels(component=component).set(memory_bytes)
        self.cpu_usage.labels(component=component).set(cpu_percent)

    # === BUSINESS METRICS HELPERS ===

    def record_profile_analysis(self, status: str):
        """Enregistrer une analyse de profil"""
        self.profiles_analyzed.labels(status=status).inc()

    def update_active_users(self, timeframe: str, count: int):
        """Mettre à jour le nombre d'utilisateurs actifs"""
        self.active_users.labels(timeframe=timeframe).set(count)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Obtenir un résumé des métriques actuelles"""
        return {
            "api_requests_5m": self._get_counter_rate(self.api_requests_total, 300),
            "rag_avg_quality": self._get_histogram_mean(self.rag_response_quality),
            "active_connections": self.api_active_connections._value._value,
            "hallucination_rate": self.rag_hallucination_rate._value._value,
            "total_profiles": sum(
                metric.samples()[0].value for metric in [self.profiles_analyzed] if metric.samples()
            ),
        }

    def _get_counter_rate(self, counter, window_seconds: int) -> float:
        """Calculer le taux d'un counter sur une fenêtre"""
        # Implémentation simplifiée - en production utiliser Prometheus query
        try:
            samples = counter.collect()[0].samples
            if samples:
                return samples[-1].value / window_seconds
        except (IndexError, AttributeError):
            pass
        return 0.0

    def _get_histogram_mean(self, histogram) -> float:
        """Calculer la moyenne d'un histogramme"""
        try:
            samples = histogram.collect()[0].samples
            sum_sample = next((s for s in samples if s.name.endswith("_sum")), None)
            count_sample = next((s for s in samples if s.name.endswith("_count")), None)

            if sum_sample and count_sample and count_sample.value > 0:
                return sum_sample.value / count_sample.value
        except (IndexError, AttributeError):
            pass
        return 0.0
