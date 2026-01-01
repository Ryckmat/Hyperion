"""
Middleware de monitoring pour FastAPI - Hyperion v3.0

Middleware pour Request ID, logging automatique, métriques et observabilité.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from hyperion.modules.monitoring.logging.json_logger import (
    get_logger,
    set_correlation_id,
    set_request_id,
)
from hyperion.settings import settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware de logging automatique pour toutes les requêtes.

    Fonctionnalités :
    - Génération automatique de Request ID
    - Logging structuré des requêtes/réponses
    - Métriques de performance automatiques
    - Corrélation ID pour traçabilité
    - Headers de monitoring
    """

    def __init__(self, app: FastAPI, logger_name: str = "hyperion.api"):
        super().__init__(app)
        self.logger = get_logger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Traite chaque requête avec logging et métriques."""
        # Générer ou récupérer les IDs
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Définir le contexte pour le thread actuel
        set_request_id(request_id)
        set_correlation_id(correlation_id)

        # Logger structuré avec contexte enrichi
        logger = self.logger.bind(
            request_id=request_id,
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )

        # Timestamp de début
        start_time = time.time()

        # Log de début de requête
        logger.info(
            "Request started",
            event_type="request_start",
            url=str(request.url),
            headers=dict(request.headers) if settings.log_level == "DEBUG" else None,
        )

        try:
            # Traitement de la requête
            response = await call_next(request)

            # Calcul des métriques
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)

            # Enrichir la réponse avec headers de monitoring
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time"] = str(duration_ms)
            response.headers["X-Service-Version"] = "3.0.0"

            # Log de fin de requête
            logger.info(
                "Request completed",
                event_type="request_complete",
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size=response.headers.get("Content-Length", "unknown"),
            )

            # Log des requêtes lentes
            if duration > 1.0:  # Plus d'1 seconde
                logger.warning(
                    "Slow request detected",
                    event_type="slow_request",
                    duration_ms=duration_ms,
                    threshold_ms=1000,
                )

            return response

        except Exception as exc:
            # Calcul du temps même en cas d'erreur
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)

            # Log de l'erreur
            logger.error(
                "Request failed",
                event_type="request_error",
                error_type=type(exc).__name__,
                error_message=str(exc),
                duration_ms=duration_ms,
                exc_info=True,
            )

            # Re-lever l'exception pour FastAPI
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extrait l'adresse IP client en tenant compte des proxies."""
        # Headers de proxy communs
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # IP directe
        return request.client.host if request.client else "unknown"


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour métriques Prometheus.

    Collecte automatiquement :
    - Nombre de requêtes par endpoint
    - Durée des requêtes (histogramme)
    - Codes de statut
    - Taille des réponses
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.metrics_enabled = settings.enable_metrics
        self._setup_metrics()

    def _setup_metrics(self):
        """Configure les métriques Prometheus."""
        if not self.metrics_enabled:
            return

        try:
            from prometheus_client import Counter, Gauge, Histogram

            # Compteur de requêtes
            self.request_count = Counter(
                "hyperion_requests_total",
                "Total requests received",
                ["method", "endpoint", "status_code"],
            )

            # Durée des requêtes
            self.request_duration = Histogram(
                "hyperion_request_duration_seconds",
                "Request duration in seconds",
                ["method", "endpoint"],
            )

            # Requêtes en cours
            self.requests_in_progress = Gauge(
                "hyperion_requests_in_progress", "Requests currently being processed"
            )

            # Taille des réponses
            self.response_size = Histogram(
                "hyperion_response_size_bytes", "Response size in bytes", ["method", "endpoint"]
            )

        except ImportError:
            self.metrics_enabled = False
            get_logger().warning("Prometheus client non disponible, métriques désactivées")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collecte les métriques pour chaque requête."""
        if not self.metrics_enabled:
            return await call_next(request)

        # Incrémenter les requêtes en cours
        self.requests_in_progress.inc()

        method = request.method
        path = request.url.path
        start_time = time.time()

        try:
            response = await call_next(request)

            # Métriques de succès
            duration = time.time() - start_time
            status_code = str(response.status_code)

            self.request_count.labels(method=method, endpoint=path, status_code=status_code).inc()

            self.request_duration.labels(method=method, endpoint=path).observe(duration)

            # Taille de la réponse si disponible
            content_length = response.headers.get("Content-Length")
            if content_length:
                self.response_size.labels(method=method, endpoint=path).observe(int(content_length))

            return response

        except Exception:
            # Métriques d'erreur
            duration = time.time() - start_time

            self.request_count.labels(method=method, endpoint=path, status_code="500").inc()

            self.request_duration.labels(method=method, endpoint=path).observe(duration)

            raise

        finally:
            # Décrémenter les requêtes en cours
            self.requests_in_progress.dec()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour headers de sécurité.

    Ajoute automatiquement des headers de sécurité recommandés :
    - Content Security Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Ajoute les headers de sécurité à chaque réponse."""
        response = await call_next(request)

        # Headers de sécurité standard
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Permitted-Cross-Domain-Policies": "none",
        }

        # Ajouter les headers à la réponse
        for header, value in security_headers.items():
            response.headers[header] = value

        return response


def setup_monitoring_middleware(app: FastAPI) -> None:
    """
    Configure tous les middlewares de monitoring.

    Args:
        app: Instance FastAPI à enrichir
    """
    # Ordre important : les middlewares sont traités en ordre inverse

    # 1. Security headers (le plus externe)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Métriques
    app.add_middleware(MetricsMiddleware)

    # 3. Request logging (le plus interne)
    app.add_middleware(RequestLoggingMiddleware)

    get_logger("hyperion.middleware").info(
        "Monitoring middleware configuré",
        middlewares=["RequestLogging", "Metrics", "SecurityHeaders"],
    )
