"""
Correlation Tracker for Hyperion v3.0

Système de corrélation pour traçabilité des requêtes distribuées.
"""

import logging
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CorrelationContext:
    """Contexte de corrélation pour une requête"""

    correlation_id: str
    parent_id: str | None = None
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str | None = None
    session_id: str | None = None
    request_path: str | None = None
    operation: str | None = None
    start_time: float = field(default_factory=time.time)
    tags: dict[str, str] = field(default_factory=dict)
    baggage: dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """Span pour tracing distribué"""

    span_id: str
    trace_id: str
    parent_span_id: str | None
    operation_name: str
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    tags: dict[str, str] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    status: str = "started"  # started, finished, error


class CorrelationTracker:
    """
    Tracker de corrélation pour Hyperion v3.0

    Fonctionnalités :
    - Génération automatique d'IDs de corrélation
    - Propagation de contexte entre threads/services
    - Spans distribués pour tracing détaillé
    - Intégration avec logs structurés
    - Métriques de performance par trace
    - Support OpenTelemetry compatible
    """

    def __init__(
        self,
        service_name: str = "hyperion",
        enable_tracing: bool = True,
        max_spans: int = 10000,
        trace_timeout: int = 3600,
    ):  # 1 heure

        self.service_name = service_name
        self.enable_tracing = enable_tracing
        self.max_spans = max_spans
        self.trace_timeout = trace_timeout

        # Storage thread-safe
        self._local = threading.local()
        self._active_spans: dict[str, Span] = {}
        self._completed_traces: dict[str, list[Span]] = {}

        # Lock pour thread-safety
        self._spans_lock = threading.Lock()

        # Background cleanup
        self._last_cleanup = time.time()

        logger.info(f"CorrelationTracker initialisé pour '{service_name}'")

    def _get_current_context(self) -> CorrelationContext | None:
        """Obtenir le contexte de corrélation actuel"""
        return getattr(self._local, "context", None)

    def _set_current_context(self, context: CorrelationContext):
        """Définir le contexte de corrélation actuel"""
        self._local.context = context

    def start_trace(
        self,
        operation: str,
        correlation_id: str | None = None,
        parent_id: str | None = None,
        **kwargs,
    ) -> str:
        """Démarrer une nouvelle trace"""

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        context = CorrelationContext(
            correlation_id=correlation_id, parent_id=parent_id, operation=operation, **kwargs
        )

        self._set_current_context(context)

        if self.enable_tracing:
            span = self._create_span(operation, context.trace_id, None)
            self._add_span_tag(span.span_id, "service.name", self.service_name)
            self._add_span_tag(span.span_id, "correlation.id", correlation_id)

        logger.debug(f"Trace démarrée: {correlation_id} pour '{operation}'")
        return correlation_id

    def get_correlation_id(self) -> str | None:
        """Obtenir l'ID de corrélation actuel"""
        context = self._get_current_context()
        return context.correlation_id if context else None

    def get_trace_id(self) -> str | None:
        """Obtenir l'ID de trace actuel"""
        context = self._get_current_context()
        return context.trace_id if context else None

    def set_user_context(self, user_id: str, session_id: str | None = None):
        """Définir le contexte utilisateur"""
        context = self._get_current_context()
        if context:
            context.user_id = user_id
            context.session_id = session_id

            # Ajouter aux spans actifs
            if self.enable_tracing:
                for span in self._active_spans.values():
                    if span.trace_id == context.trace_id:
                        span.tags["user.id"] = user_id
                        if session_id:
                            span.tags["session.id"] = session_id

    def add_baggage(self, key: str, value: Any):
        """Ajouter des données baggage (propagées entre services)"""
        context = self._get_current_context()
        if context:
            context.baggage[key] = value

    def get_baggage(self, key: str) -> Any:
        """Récupérer une donnée baggage"""
        context = self._get_current_context()
        return context.baggage.get(key) if context else None

    @contextmanager
    def span(self, operation_name: str, **tags):
        """Context manager pour créer un span"""
        context = self._get_current_context()
        if not context or not self.enable_tracing:
            # Pas de tracing actif, juste exécuter l'opération
            yield None
            return

        span = self._create_span(operation_name, context.trace_id, context.span_id)

        # Ajouter les tags
        for key, value in tags.items():
            self._add_span_tag(span.span_id, key, str(value))

        # Mettre à jour le contexte avec le nouveau span
        old_span_id = context.span_id
        context.span_id = span.span_id

        try:
            yield span
            self._finish_span(span.span_id, "finished")
        except Exception as e:
            self._finish_span(span.span_id, "error")
            self._add_span_log(
                span.span_id,
                "error",
                {"event": "error", "error.kind": type(e).__name__, "message": str(e)},
            )
            raise
        finally:
            # Restaurer le span parent
            context.span_id = old_span_id

    def _create_span(self, operation_name: str, trace_id: str, parent_span_id: str | None) -> Span:
        """Créer un nouveau span"""
        span = Span(
            span_id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=time.time(),
        )

        with self._spans_lock:
            self._active_spans[span.span_id] = span

            # Nettoyage si nécessaire
            if len(self._active_spans) > self.max_spans:
                self._cleanup_old_spans()

        return span

    def _finish_span(self, span_id: str, status: str):
        """Terminer un span"""
        with self._spans_lock:
            span = self._active_spans.get(span_id)
            if span:
                span.end_time = time.time()
                span.duration = span.end_time - span.start_time
                span.status = status

                # Déplacer vers les traces complétées
                if span.trace_id not in self._completed_traces:
                    self._completed_traces[span.trace_id] = []

                self._completed_traces[span.trace_id].append(span)
                del self._active_spans[span_id]

    def _add_span_tag(self, span_id: str, key: str, value: str):
        """Ajouter un tag à un span"""
        with self._spans_lock:
            span = self._active_spans.get(span_id)
            if span:
                span.tags[key] = value

    def _add_span_log(self, span_id: str, level: str, fields: dict[str, Any]):
        """Ajouter un log à un span"""
        with self._spans_lock:
            span = self._active_spans.get(span_id)
            if span:
                log_entry = {"timestamp": time.time(), "level": level, "fields": fields}
                span.logs.append(log_entry)

    def log_event(self, message: str, level: str = "info", **fields):
        """Logger un événement dans le span actuel"""
        context = self._get_current_context()
        if context and context.span_id and self.enable_tracing:
            self._add_span_log(context.span_id, level, {"event": message, **fields})

    def finish_trace(self) -> dict[str, Any] | None:
        """Terminer la trace actuelle"""
        context = self._get_current_context()
        if not context:
            return None

        correlation_id = context.correlation_id
        trace_id = context.trace_id

        # Terminer tous les spans actifs de cette trace
        if self.enable_tracing:
            with self._spans_lock:
                active_trace_spans = [
                    span for span in self._active_spans.values() if span.trace_id == trace_id
                ]

                for span in active_trace_spans:
                    self._finish_span(span.span_id, "finished")

        # Calculer les métriques de trace
        trace_summary = self._get_trace_summary(trace_id)

        # Nettoyer le contexte
        self._local.context = None

        logger.debug(f"Trace terminée: {correlation_id}")
        return trace_summary

    def get_trace_summary(self, trace_id: str | None = None) -> dict[str, Any] | None:
        """Obtenir le résumé d'une trace"""
        if not trace_id:
            context = self._get_current_context()
            trace_id = context.trace_id if context else None

        if not trace_id:
            return None

        return self._get_trace_summary(trace_id)

    def _get_trace_summary(self, trace_id: str) -> dict[str, Any]:
        """Calculer le résumé d'une trace"""
        with self._spans_lock:
            spans = self._completed_traces.get(trace_id, [])
            active_spans = [s for s in self._active_spans.values() if s.trace_id == trace_id]
            all_spans = spans + active_spans

        if not all_spans:
            return {"trace_id": trace_id, "spans": 0}

        total_duration = 0
        operations = set()
        error_count = 0

        for span in spans:  # Seulement les spans terminés pour les métriques
            if span.duration:
                total_duration += span.duration
            operations.add(span.operation_name)
            if span.status == "error":
                error_count += 1

        return {
            "trace_id": trace_id,
            "spans_completed": len(spans),
            "spans_active": len(active_spans),
            "total_duration": total_duration,
            "operations": list(operations),
            "error_count": error_count,
            "success_rate": (len(spans) - error_count) / len(spans) if spans else 1.0,
        }

    def _cleanup_old_spans(self):
        """Nettoyer les anciens spans et traces"""
        current_time = time.time()
        cutoff_time = current_time - self.trace_timeout

        # Nettoyer les spans actifs trop anciens
        old_spans = [
            span_id for span_id, span in self._active_spans.items() if span.start_time < cutoff_time
        ]

        for span_id in old_spans:
            self._finish_span(span_id, "timeout")

        # Nettoyer les traces complétées anciennes
        old_traces = [
            trace_id
            for trace_id, spans in self._completed_traces.items()
            if spans and spans[0].start_time < cutoff_time
        ]

        for trace_id in old_traces:
            del self._completed_traces[trace_id]

        if old_spans or old_traces:
            logger.debug(f"Nettoyage: {len(old_spans)} spans, {len(old_traces)} traces")

    def get_active_traces(self) -> list[dict[str, Any]]:
        """Obtenir toutes les traces actives"""
        with self._spans_lock:
            active_trace_ids = {span.trace_id for span in self._active_spans.values()}

        return [self._get_trace_summary(trace_id) for trace_id in active_trace_ids]

    def export_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Exporter une trace complète (format compatible OpenTelemetry)"""
        with self._spans_lock:
            spans = self._completed_traces.get(trace_id, [])

        if not spans:
            return None

        return {
            "traceId": trace_id,
            "serviceName": self.service_name,
            "spans": [
                {
                    "spanId": span.span_id,
                    "parentSpanId": span.parent_span_id,
                    "operationName": span.operation_name,
                    "startTime": span.start_time,
                    "endTime": span.end_time,
                    "duration": span.duration,
                    "status": span.status,
                    "tags": span.tags,
                    "logs": span.logs,
                }
                for span in spans
            ],
        }


# Instance globale
correlation_tracker = CorrelationTracker()


# Fonctions de convenance
def start_trace(operation: str, **kwargs) -> str:
    """Démarrer une nouvelle trace"""
    return correlation_tracker.start_trace(operation, **kwargs)


def get_correlation_id() -> str | None:
    """Obtenir l'ID de corrélation actuel"""
    return correlation_tracker.get_correlation_id()


def span(operation_name: str, **tags):
    """Context manager pour créer un span"""
    return correlation_tracker.span(operation_name, **tags)
