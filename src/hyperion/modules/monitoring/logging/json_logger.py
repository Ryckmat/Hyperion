"""
JSON Logger amélioré avec structlog pour Hyperion v3.0

Intégration de structlog pour un logging encore plus structuré et performant.
"""

from __future__ import annotations

import os
import threading
import uuid
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from hyperion.settings import settings


def configure_structlog() -> None:
    """
    Configure structlog pour Hyperion v3.0

    Configuration optimisée pour :
    - JSON structuré en production
    - Format lisible en développement
    - Performance élevée avec cache
    - Intégration Request ID automatique
    """
    # Processeurs communs
    shared_processors = [
        # Filtrer les paramètres sensibles
        structlog.stdlib.filter_by_level,
        # Ajouter le nom du logger
        structlog.stdlib.add_logger_name,
        # Ajouter le niveau de log
        structlog.stdlib.add_log_level,
        # Ajouter le timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Ajouter les informations de stack (uniquement pour erreurs)
        structlog.processors.StackInfoRenderer(),
        # Formatter les exceptions
        structlog.processors.format_exc_info,
    ]

    # Processeurs spécifiques à l'environnement
    if settings.log_level == "DEBUG" or os.getenv("HYPERION_DEV", "false").lower() == "true":
        # Mode développement : format lisible avec couleurs
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=True)]
    else:
        # Mode production : JSON structuré
        processors = shared_processors + [
            # Ajouter des métadonnées système
            add_system_metadata,
            # Renommer les clés pour compatibilité
            structlog.processors.dict_tracebacks,
            # Renderer JSON
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ]

    # Configuration structlog
    structlog.configure(
        processors=processors,
        wrapper_class=make_filtering_bound_logger(settings.log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def make_filtering_bound_logger(min_level: str):
    """Crée un BoundLogger avec filtrage de niveau."""

    class FilteringBoundLogger(BoundLogger):
        def __init__(self, logger, processors=None, context=None):
            super().__init__(logger, processors, context)
            self.min_level = getattr(structlog.stdlib.logging, min_level.upper(), 20)

        def debug(self, event, **kw):
            if self.min_level <= 10:
                super().debug(event, **kw)

        def info(self, event, **kw):
            if self.min_level <= 20:
                super().info(event, **kw)

        def warning(self, event, **kw):
            if self.min_level <= 30:
                super().warning(event, **kw)

        def error(self, event, **kw):
            if self.min_level <= 40:
                super().error(event, **kw)

        def critical(self, event, **kw):
            if self.min_level <= 50:
                super().critical(event, **kw)

    return FilteringBoundLogger


def add_system_metadata(_logger, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Ajoute des métadonnées système aux logs.

    Args:
        logger: Logger instance
        method_name: Nom de la méthode de logging
        event_dict: Dictionnaire d'événement à enrichir

    Returns:
        Dictionnaire enrichi avec métadonnées système
    """
    # Métadonnées Hyperion
    event_dict.update(
        {
            "service": "hyperion",
            "version": "3.0.0",
            "environment": os.getenv("HYPERION_ENV", "development"),
            "hostname": os.getenv("HOSTNAME", "unknown"),
            "pid": os.getpid(),
        }
    )

    # Request ID depuis contexte (défini par middleware)
    request_id = get_current_request_id()
    if request_id:
        event_dict["request_id"] = request_id

    # Correlation ID depuis contexte
    correlation_id = get_current_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id

    return event_dict


# Variables thread-local pour contexte
_context = threading.local()


def set_request_id(request_id: str) -> None:
    """Définit l'ID de requête pour le thread actuel."""
    _context.request_id = request_id


def get_current_request_id() -> str | None:
    """Obtient l'ID de requête du thread actuel."""
    return getattr(_context, "request_id", None)


def set_correlation_id(correlation_id: str) -> None:
    """Définit l'ID de corrélation pour le thread actuel."""
    _context.correlation_id = correlation_id


def get_current_correlation_id() -> str | None:
    """Obtient l'ID de corrélation du thread actuel."""
    return getattr(_context, "correlation_id", None)


def generate_correlation_id() -> str:
    """Génère un nouvel ID de corrélation."""
    return str(uuid.uuid4())


class StructlogAdapter:
    """
    Adaptateur pour rendre structlog compatible avec l'API standard.

    Permet d'utiliser structlog avec l'interface logging standard
    tout en gardant les avantages de la structure.
    """

    def __init__(self, logger_name: str = "hyperion"):
        self.logger = structlog.get_logger(logger_name)

    def debug(self, msg: str, *args, **kwargs):
        """Log debug avec format compatible."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info avec format compatible."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning avec format compatible."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, exc_info=None, **kwargs):
        """Log error avec support exc_info."""
        if exc_info:
            kwargs["exc_info"] = exc_info
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical avec format compatible."""
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log exception avec traceback automatique."""
        kwargs["exc_info"] = True
        self.logger.error(msg, *args, **kwargs)

    def bind(self, **kwargs):
        """Bind context au logger (interface structlog)."""
        return self.logger.bind(**kwargs)


def get_logger(name: str = "hyperion") -> StructlogAdapter:
    """
    Obtient un logger structlog configuré.

    Args:
        name: Nom du logger

    Returns:
        Logger structuré configuré
    """
    return StructlogAdapter(name)


# Configuration automatique au chargement du module
configure_structlog()

# Logger par défaut
logger = get_logger()
