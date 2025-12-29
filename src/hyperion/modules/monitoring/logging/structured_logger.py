"""
Structured Logger for Hyperion v3.0

Logging structuré avec contexte, corrélation et intégration monitoring.
"""

import json
import logging
import threading
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LogLevel(Enum):
    """Niveaux de log étendus pour Hyperion"""

    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    FATAL = 50
    AUDIT = 60  # Logs d'audit spéciaux


@dataclass
class LogContext:
    """Contexte enrichi pour logs structurés"""

    correlation_id: str
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None
    operation: str | None = None
    component: str | None = None
    version: str = "3.0.0-dev"
    environment: str = "development"
    custom_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class LogEntry:
    """Entrée de log structurée"""

    timestamp: str
    level: str
    message: str
    logger_name: str
    context: LogContext
    exception: dict[str, str] | None = None
    performance: dict[str, float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class StructuredLogger:
    """
    Logger structuré enterprise pour Hyperion v3.0

    Fonctionnalités :
    - Logs structurés JSON avec contexte enrichi
    - Corrélation automatique des requêtes
    - Intégration métriques de performance
    - Support audit trail
    - Buffering intelligent pour performance
    - Formatters configurables (JSON, human-readable)
    """

    def __init__(
        self,
        name: str = "hyperion",
        level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        file_path: str | None = None,
        enable_json_format: bool = True,
        buffer_size: int = 1000,
    ):

        self.name = name
        self.level = level
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json_format = enable_json_format
        self.buffer_size = buffer_size

        # Thread-local storage pour contexte
        self._local = threading.local()

        # Buffer pour logs haute performance
        self._log_buffer: list[LogEntry] = []
        self._buffer_lock = threading.Lock()

        # Configuration des handlers
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level.value)
        self._setup_handlers(file_path)

        # Callbacks pour intégrations externes
        self._external_handlers: list[callable] = []

        self._logger.info(f"StructuredLogger '{name}' initialisé")

    def _setup_handlers(self, file_path: str | None):
        """Configurer les handlers de logging"""

        # Éviter les handlers dupliqués
        self._logger.handlers.clear()

        # Formatter JSON structuré
        if self.enable_json_format:
            formatter = self._create_json_formatter()
        else:
            formatter = self._create_human_formatter()

        # Handler console
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

        # Handler fichier
        if self.enable_file:
            if not file_path:
                file_path = f"logs/hyperion_{datetime.now().strftime('%Y%m%d')}.log"

            try:
                import os

                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file_handler = logging.FileHandler(file_path)
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)
            except Exception as e:
                self._logger.error(f"Impossible de créer le handler fichier: {e}")

    def _create_json_formatter(self):
        """Créer un formatter JSON structuré"""
        logger_instance = self

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                # Enrichir le record avec le contexte Hyperion
                log_entry = logger_instance._create_log_entry(record)
                return json.dumps(asdict(log_entry), ensure_ascii=False, default=str)

        return JSONFormatter()

    def _create_human_formatter(self):
        """Créer un formatter lisible pour développement"""
        return logging.Formatter(
            "%(asctime)s | %(levelname)-5s | %(name)s | %(correlation_id)s | %(message)s"
        )

    def _create_log_entry(self, record) -> LogEntry:
        """Créer une entrée de log structurée"""
        context = self.get_context()

        # Extraire les informations d'exception si présentes
        exception_info = None
        if record.exc_info:
            exception_info = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Extraire les métriques de performance si présentes
        performance_info = None
        if hasattr(record, "duration"):
            performance_info = {
                "duration_ms": record.duration * 1000,
                "memory_mb": getattr(record, "memory_mb", 0),
                "cpu_percent": getattr(record, "cpu_percent", 0),
            }

        return LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            context=context,
            exception=exception_info,
            performance=performance_info,
            metadata={
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "thread": record.thread,
                "process": record.process,
            },
        )

    def set_context(self, **kwargs):
        """Définir le contexte de logging pour le thread actuel"""
        if not hasattr(self._local, "context"):
            self._local.context = LogContext(correlation_id=str(uuid.uuid4()))

        for key, value in kwargs.items():
            if hasattr(self._local.context, key):
                setattr(self._local.context, key, value)
            else:
                self._local.context.custom_fields[key] = value

    def get_context(self) -> LogContext:
        """Obtenir le contexte actuel"""
        if not hasattr(self._local, "context"):
            self._local.context = LogContext(correlation_id=str(uuid.uuid4()))
        return self._local.context

    @contextmanager
    def context_manager(self, **kwargs):
        """Context manager pour contexte temporaire"""
        old_context = getattr(self._local, "context", None)
        try:
            self.set_context(**kwargs)
            yield
        finally:
            self._local.context = old_context

    def trace(self, message: str, **kwargs):
        """Log trace (très détaillé)"""
        self._log(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug"""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info"""
        self._log(LogLevel.INFO, message, **kwargs)

    def warn(self, message: str, **kwargs):
        """Log warning"""
        self._log(LogLevel.WARN, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Alias pour warn"""
        self.warn(message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error avec support exception"""
        self._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    def fatal(self, message: str, exc_info: bool = True, **kwargs):
        """Log fatal (critique)"""
        self._log(LogLevel.FATAL, message, exc_info=exc_info, **kwargs)

    def audit(self, action: str, resource: str, result: str, **kwargs):
        """Log d'audit sécurisé"""
        message = f"AUDIT: {action} on {resource} -> {result}"
        self._log(LogLevel.AUDIT, message, **kwargs)

    def _log(self, level: LogLevel, message: str, exc_info: bool = False, **kwargs):
        """Méthode de logging interne"""
        if level.value < self.level.value:
            return

        # Enrichir le contexte avec les kwargs
        extra = {}
        context = self.get_context()

        # Ajouter les métriques de performance si disponibles
        if "duration" in kwargs:
            extra["duration"] = kwargs.pop("duration")
        if "memory_mb" in kwargs:
            extra["memory_mb"] = kwargs.pop("memory_mb")
        if "cpu_percent" in kwargs:
            extra["cpu_percent"] = kwargs.pop("cpu_percent")

        # Ajouter le correlation_id au extra pour les formatters standards
        extra["correlation_id"] = context.correlation_id

        # Logger standard
        self._logger.log(level.value, message, exc_info=exc_info, extra=extra)

        # Appeler les handlers externes
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.name,
            message=message,
            logger_name=self.name,
            context=context,
            metadata=kwargs,
        )

        for handler in self._external_handlers:
            try:
                handler(log_entry)
            except Exception as e:
                self._logger.error(f"Erreur handler externe: {e}")

    def log_performance(
        self,
        operation: str,
        duration: float,
        memory_mb: float = 0,
        cpu_percent: float = 0,
        **kwargs,
    ):
        """Logger les métriques de performance"""
        self.info(
            f"Performance: {operation} completed",
            duration=duration,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            operation=operation,
            **kwargs,
        )

    @contextmanager
    def track_operation(self, operation: str, **context_kwargs):
        """Tracker une opération avec logging automatique"""
        start_time = time.time()

        with self.context_manager(operation=operation, **context_kwargs):
            self.debug(f"Starting operation: {operation}")
            try:
                yield
                duration = time.time() - start_time
                self.log_performance(operation, duration)
                self.info(f"Operation completed: {operation}")
            except Exception:
                duration = time.time() - start_time
                self.error(
                    f"Operation failed: {operation}",
                    exc_info=True,
                    duration=duration,
                    operation=operation,
                )
                raise

    def add_external_handler(self, handler: callable):
        """Ajouter un handler externe (ex: envoi vers monitoring)"""
        self._external_handlers.append(handler)

    def get_log_stats(self) -> dict[str, Any]:
        """Obtenir les statistiques de logging"""
        return {
            "name": self.name,
            "level": self.level.name,
            "handlers_count": len(self._logger.handlers),
            "external_handlers": len(self._external_handlers),
            "current_context": asdict(self.get_context()),
        }


# Instance globale par défaut
default_logger = StructuredLogger()


# Fonctions de convenance
def get_logger(name: str = "hyperion") -> StructuredLogger:
    """Obtenir une instance de logger structuré"""
    return StructuredLogger(name=name)


def set_global_context(**kwargs):
    """Définir le contexte global"""
    default_logger.set_context(**kwargs)


def log_operation(operation: str):
    """Décorateur pour tracker automatiquement les opérations"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with default_logger.track_operation(operation):
                return func(*args, **kwargs)

        return wrapper

    return decorator
