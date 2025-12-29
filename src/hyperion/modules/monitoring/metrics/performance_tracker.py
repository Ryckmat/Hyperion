"""
Performance Tracker for Hyperion v3.0

Suivi de performance en temps réel avec analytics intelligents.
"""

import functools
import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Métriques de performance"""

    timestamp: float
    operation: str
    duration: float
    cpu_percent: float
    memory_mb: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """Utilisation des ressources système"""

    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int


class PerformanceTracker:
    """
    Tracker de performance pour Hyperion v3.0

    Fonctionnalités :
    - Suivi temps réel des opérations
    - Profiling automatique des fonctions
    - Détection d'anomalies de performance
    - Analytics de tendances
    - Integration avec monitoring
    """

    def __init__(self, buffer_size: int = 10000, enable_system_monitoring: bool = True):
        self.buffer_size = buffer_size
        self.enable_system_monitoring = enable_system_monitoring

        # Stockage des métriques
        self.metrics_buffer: deque = deque(maxlen=buffer_size)
        self.operation_stats: dict[str, list[float]] = defaultdict(list)

        # Seuils d'alerte
        self.performance_thresholds = {
            "api_request_slow": 1.0,  # secondes
            "rag_query_slow": 5.0,
            "ml_prediction_slow": 2.0,
            "memory_high": 85.0,  # pourcentage
            "cpu_high": 80.0,
        }

        # Callbacks pour alertes
        self.alert_callbacks: list[Callable] = []

        # Monitoring système
        self._system_monitor_active = False
        self._system_monitor_thread = None

        if enable_system_monitoring:
            self.start_system_monitoring()

        logger.info("PerformanceTracker initialisé")

    def start_system_monitoring(self, interval: float = 5.0):
        """Démarrer le monitoring système en arrière-plan"""
        if self._system_monitor_active:
            return

        self._system_monitor_active = True
        self._system_monitor_thread = threading.Thread(
            target=self._system_monitor_loop, args=(interval,), daemon=True
        )
        self._system_monitor_thread.start()
        logger.info("Monitoring système démarré")

    def stop_system_monitoring(self):
        """Arrêter le monitoring système"""
        self._system_monitor_active = False
        if self._system_monitor_thread:
            self._system_monitor_thread.join(timeout=1.0)
        logger.info("Monitoring système arrêté")

    def _system_monitor_loop(self, interval: float):
        """Boucle de monitoring système"""
        while self._system_monitor_active:
            try:
                usage = self._get_resource_usage()
                self._check_resource_alerts(usage)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Erreur monitoring système: {e}")
                time.sleep(interval)

    def _get_resource_usage(self) -> ResourceUsage:
        """Obtenir l'utilisation actuelle des ressources"""
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()

        return ResourceUsage(
            cpu_percent=cpu,
            memory_percent=memory.percent,
            memory_mb=memory.used / (1024 * 1024),
            disk_io_read=disk_io.read_bytes if disk_io else 0,
            disk_io_write=disk_io.write_bytes if disk_io else 0,
            network_sent=net_io.bytes_sent if net_io else 0,
            network_recv=net_io.bytes_recv if net_io else 0,
        )

    def _check_resource_alerts(self, usage: ResourceUsage):
        """Vérifier les seuils d'alerte ressources"""
        alerts = []

        if usage.cpu_percent > self.performance_thresholds["cpu_high"]:
            alerts.append(
                {
                    "type": "cpu_high",
                    "value": usage.cpu_percent,
                    "threshold": self.performance_thresholds["cpu_high"],
                    "message": f"CPU usage high: {usage.cpu_percent:.1f}%",
                }
            )

        if usage.memory_percent > self.performance_thresholds["memory_high"]:
            alerts.append(
                {
                    "type": "memory_high",
                    "value": usage.memory_percent,
                    "threshold": self.performance_thresholds["memory_high"],
                    "message": f"Memory usage high: {usage.memory_percent:.1f}%",
                }
            )

        for alert in alerts:
            self._trigger_alert(alert)

    @contextmanager
    def track_operation(self, operation: str, metadata: dict | None = None):
        """Context manager pour tracker une opération"""
        start_time = time.time()
        start_usage = self._get_resource_usage() if self.enable_system_monitoring else None
        success = True

        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time

            # Calculer l'usage des ressources
            if start_usage and self.enable_system_monitoring:
                end_usage = self._get_resource_usage()
                cpu_percent = end_usage.cpu_percent
                memory_mb = end_usage.memory_mb - start_usage.memory_mb
            else:
                cpu_percent = 0.0
                memory_mb = 0.0

            # Créer les métriques
            metrics = PerformanceMetrics(
                timestamp=end_time,
                operation=operation,
                duration=duration,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                success=success,
                metadata=metadata or {},
            )

            self._record_metrics(metrics)

    def track_function(self, operation: str = None, track_args: bool = False):
        """Décorateur pour tracker automatiquement les fonctions"""

        def decorator(func):
            op_name = operation or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                metadata = {}
                if track_args:
                    metadata["args_count"] = len(args)
                    metadata["kwargs_keys"] = list(kwargs.keys())

                with self.track_operation(op_name, metadata):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def _record_metrics(self, metrics: PerformanceMetrics):
        """Enregistrer les métriques"""
        # Ajouter au buffer
        self.metrics_buffer.append(metrics)

        # Mettre à jour les stats par opération
        self.operation_stats[metrics.operation].append(metrics.duration)

        # Garder seulement les 1000 dernières mesures par opération
        if len(self.operation_stats[metrics.operation]) > 1000:
            self.operation_stats[metrics.operation] = self.operation_stats[metrics.operation][
                -1000:
            ]

        # Vérifier les seuils de performance
        self._check_performance_alerts(metrics)

        logger.debug(f"Métrique enregistrée: {metrics.operation} en {metrics.duration:.3f}s")

    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """Vérifier les seuils d'alerte de performance"""
        operation_type = self._classify_operation(metrics.operation)
        threshold_key = f"{operation_type}_slow"

        if threshold_key in self.performance_thresholds:
            threshold = self.performance_thresholds[threshold_key]
            if metrics.duration > threshold:
                alert = {
                    "type": "performance_slow",
                    "operation": metrics.operation,
                    "duration": metrics.duration,
                    "threshold": threshold,
                    "message": f"Slow operation: {metrics.operation} took {metrics.duration:.2f}s",
                }
                self._trigger_alert(alert)

    def _classify_operation(self, operation: str) -> str:
        """Classifier le type d'opération"""
        if "api" in operation.lower() or "endpoint" in operation.lower():
            return "api_request"
        elif "rag" in operation.lower() or "query" in operation.lower():
            return "rag_query"
        elif "ml" in operation.lower() or "predict" in operation.lower():
            return "ml_prediction"
        return "other"

    def _trigger_alert(self, alert: dict):
        """Déclencher une alerte"""
        logger.warning(f"Performance Alert: {alert['message']}")

        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erreur callback alerte: {e}")

    def add_alert_callback(self, callback: Callable):
        """Ajouter un callback pour les alertes"""
        self.alert_callbacks.append(callback)

    def get_operation_stats(self, operation: str) -> dict[str, float]:
        """Obtenir les statistiques d'une opération"""
        durations = self.operation_stats.get(operation, [])
        if not durations:
            return {}

        durations_sorted = sorted(durations)
        count = len(durations_sorted)

        return {
            "count": count,
            "avg": sum(durations_sorted) / count,
            "min": durations_sorted[0],
            "max": durations_sorted[-1],
            "median": durations_sorted[count // 2],
            "p95": durations_sorted[int(count * 0.95)] if count > 0 else 0,
            "p99": durations_sorted[int(count * 0.99)] if count > 0 else 0,
        }

    def get_performance_summary(self, window_seconds: int = 300) -> dict[str, Any]:
        """Obtenir un résumé de performance sur une fenêtre de temps"""
        cutoff_time = time.time() - window_seconds
        recent_metrics = [m for m in self.metrics_buffer if m.timestamp > cutoff_time]

        if not recent_metrics:
            return {}

        # Grouper par opération
        operations = defaultdict(list)
        for m in recent_metrics:
            operations[m.operation].append(m)

        summary = {
            "window_seconds": window_seconds,
            "total_operations": len(recent_metrics),
            "operations": {},
        }

        for op, metrics in operations.items():
            durations = [m.duration for m in metrics]
            success_count = sum(1 for m in metrics if m.success)

            summary["operations"][op] = {
                "count": len(metrics),
                "success_rate": success_count / len(metrics) if metrics else 0,
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
            }

        return summary

    def get_slowest_operations(self, limit: int = 10) -> list[dict[str, Any]]:
        """Obtenir les opérations les plus lentes récentes"""
        if not self.metrics_buffer:
            return []

        # Trier par durée décroissante
        slowest = sorted(self.metrics_buffer, key=lambda m: m.duration, reverse=True)[:limit]

        return [
            {
                "operation": m.operation,
                "duration": m.duration,
                "timestamp": m.timestamp,
                "success": m.success,
                "metadata": m.metadata,
            }
            for m in slowest
        ]

    def clear_metrics(self):
        """Vider les métriques stockées"""
        self.metrics_buffer.clear()
        self.operation_stats.clear()
        logger.info("Métriques de performance effacées")

    def export_metrics(self, format: str = "json") -> str:
        """Exporter les métriques dans différents formats"""
        if format == "json":
            import json

            data = {
                "operations_stats": {
                    op: self.get_operation_stats(op) for op in self.operation_stats
                },
                "recent_summary": self.get_performance_summary(),
                "slowest_operations": self.get_slowest_operations(),
            }
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Format non supporté: {format}")

    def __enter__(self):
        """Support du context manager pour usage simple"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup automatique"""
        self.stop_system_monitoring()
