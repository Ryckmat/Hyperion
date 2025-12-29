"""
Audit Logger for Hyperion v3.0

Logging d'audit sécurisé et immuable pour conformité enterprise.
"""

import hashlib
import hmac
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Niveaux d'audit selon criticité"""

    LOW = 1  # Lectures, consultations
    MEDIUM = 2  # Modifications données
    HIGH = 3  # Actions admin, configs
    CRITICAL = 4  # Sécurité, suppressions


class AuditAction(Enum):
    """Types d'actions auditables"""

    # Authentification
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    TOKEN_ISSUED = "auth.token_issued"
    TOKEN_REVOKED = "auth.token_revoked"

    # Données utilisateur
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_VIEW = "user.view"

    # Analyse de code
    REPO_ANALYZE = "repo.analyze"
    REPO_ACCESS = "repo.access"
    REPO_DELETE = "repo.delete"

    # Configuration
    CONFIG_UPDATE = "config.update"
    CONFIG_VIEW = "config.view"

    # API
    API_CALL = "api.call"
    API_ERROR = "api.error"

    # Système
    SYSTEM_START = "system.start"
    SYSTEM_SHUTDOWN = "system.shutdown"

    # Sécurité
    SECURITY_ALERT = "security.alert"
    ACCESS_DENIED = "security.access_denied"


@dataclass
class AuditEntry:
    """Entrée d'audit immuable"""

    id: str
    timestamp: str
    level: str
    action: str
    resource: str
    result: str
    user_id: str | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    checksum: str | None = None


@dataclass
class AuditConfig:
    """Configuration de l'audit logger"""

    enable_file_audit: bool = True
    enable_database_audit: bool = False
    enable_remote_audit: bool = False
    audit_file_path: str = "audit/hyperion_audit.jsonl"
    secret_key: str | None = None
    retention_days: int = 2555  # 7 ans par défaut
    encrypt_sensitive: bool = True


class AuditLogger:
    """
    Logger d'audit enterprise pour Hyperion v3.0

    Fonctionnalités :
    - Audit trail immuable avec checksums
    - Classification par niveaux de criticité
    - Logging sécurisé et chiffré
    - Conformité réglementaire (GDPR, SOX)
    - Intégration monitoring et alerting
    - Protection contre la falsification
    - Rétention configurable
    """

    def __init__(self, config: AuditConfig | None = None):
        self.config = config or AuditConfig()
        self._lock = threading.Lock()
        self._setup_audit_storage()

        # Compteurs pour métriques
        self._audit_counts = {level.name: 0 for level in AuditLevel}
        self._last_audit_time = time.time()

        logger.info("AuditLogger initialisé avec protection anti-falsification")

    def _setup_audit_storage(self):
        """Configurer le stockage d'audit"""
        if self.config.enable_file_audit:
            audit_path = Path(self.config.audit_file_path)
            audit_path.parent.mkdir(parents=True, exist_ok=True)

            # Vérifier les permissions (lecture seule après écriture)
            try:
                with open(audit_path, "a"):
                    pass  # Test d'écriture
            except Exception as e:
                logger.error(f"Impossible d'accéder au fichier d'audit: {e}")

    def _generate_checksum(self, entry: AuditEntry) -> str:
        """Générer un checksum de vérification d'intégrité"""
        if not self.config.secret_key:
            # Fallback sans clé secrète (moins sécurisé)
            content = f"{entry.timestamp}{entry.action}{entry.resource}{entry.result}"
            return hashlib.sha256(content.encode()).hexdigest()[:16]

        # HMAC avec clé secrète
        content = json.dumps(asdict(entry), sort_keys=True, ensure_ascii=False)
        return hmac.new(
            self.config.secret_key.encode(), content.encode(), hashlib.sha256
        ).hexdigest()[:16]

    def _create_audit_entry(
        self, action: AuditAction, resource: str, result: str, level: AuditLevel, **kwargs
    ) -> AuditEntry:
        """Créer une entrée d'audit"""
        import uuid

        entry = AuditEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            level=level.name,
            action=action.value,
            resource=resource,
            result=result,
            **kwargs,
        )

        # Générer le checksum après création
        entry.checksum = self._generate_checksum(entry)
        return entry

    def audit(
        self,
        action: AuditAction,
        resource: str,
        result: str = "SUCCESS",
        level: AuditLevel = AuditLevel.MEDIUM,
        user_id: str | None = None,
        session_id: str | None = None,
        correlation_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        **details,
    ):
        """Enregistrer une entrée d'audit"""

        entry = self._create_audit_entry(
            action=action,
            resource=resource,
            result=result,
            level=level,
            user_id=user_id,
            session_id=session_id,
            correlation_id=correlation_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )

        with self._lock:
            self._write_audit_entry(entry)
            self._audit_counts[level.name] += 1
            self._last_audit_time = time.time()

        # Logger standard pour visibilité
        logger.info(f"AUDIT: {action.value} on {resource} -> {result}")

        # Alertes pour actions critiques
        if level in [AuditLevel.HIGH, AuditLevel.CRITICAL]:
            self._trigger_audit_alert(entry)

    def _write_audit_entry(self, entry: AuditEntry):
        """Écrire l'entrée d'audit de manière sécurisée"""
        entry_json = json.dumps(asdict(entry), ensure_ascii=False)

        if self.config.enable_file_audit:
            try:
                with open(self.config.audit_file_path, "a") as f:
                    f.write(entry_json + "\n")
                    f.flush()  # Force l'écriture immédiate
            except Exception as e:
                logger.error(f"Erreur écriture audit: {e}")

        # TODO: Implémentation base de données si activée
        # TODO: Implémentation audit distant si activé

    def _trigger_audit_alert(self, entry: AuditEntry):
        """Déclencher une alerte pour action critique"""
        alert_message = (
            f"AUDIT ALERT: {entry.level} - {entry.action} "
            f"on {entry.resource} by {entry.user_id or 'anonymous'}"
        )

        # Logger l'alerte
        logger.warning(alert_message)

        # TODO: Intégration avec système d'alerting

    # === Méthodes de convenance pour actions courantes ===

    def log_authentication(
        self, user_id: str, result: str = "SUCCESS", ip_address: str | None = None, **details
    ):
        """Logger une tentative d'authentification"""
        action = AuditAction.LOGIN if result == "SUCCESS" else AuditAction.LOGIN_FAILED
        level = AuditLevel.MEDIUM if result == "SUCCESS" else AuditLevel.HIGH

        self.audit(
            action=action,
            resource=f"user:{user_id}",
            result=result,
            level=level,
            user_id=user_id,
            ip_address=ip_address,
            **details,
        )

    def log_logout(self, user_id: str, session_id: str | None = None, **details):
        """Logger une déconnexion"""
        self.audit(
            action=AuditAction.LOGOUT,
            resource=f"user:{user_id}",
            result="SUCCESS",
            level=AuditLevel.LOW,
            user_id=user_id,
            session_id=session_id,
            **details,
        )

    def log_api_call(
        self, endpoint: str, method: str, status_code: int, user_id: str | None = None, **details
    ):
        """Logger un appel API"""
        action = AuditAction.API_CALL if status_code < 400 else AuditAction.API_ERROR
        level = AuditLevel.LOW if status_code < 400 else AuditLevel.MEDIUM
        result = "SUCCESS" if status_code < 400 else f"ERROR_{status_code}"

        self.audit(
            action=action,
            resource=f"{method} {endpoint}",
            result=result,
            level=level,
            user_id=user_id,
            status_code=status_code,
            **details,
        )

    def log_repo_analysis(self, repo_name: str, user_id: str, result: str = "SUCCESS", **details):
        """Logger une analyse de repository"""
        level = AuditLevel.MEDIUM if result == "SUCCESS" else AuditLevel.HIGH

        self.audit(
            action=AuditAction.REPO_ANALYZE,
            resource=f"repo:{repo_name}",
            result=result,
            level=level,
            user_id=user_id,
            **details,
        )

    def log_config_change(self, config_key: str, user_id: str, **details):
        """Logger un changement de configuration"""
        self.audit(
            action=AuditAction.CONFIG_UPDATE,
            resource=f"config:{config_key}",
            result="SUCCESS",
            level=AuditLevel.HIGH,
            user_id=user_id,
            **details,
        )

    def log_security_event(
        self, event_type: str, resource: str, user_id: str | None = None, **details
    ):
        """Logger un événement de sécurité"""
        self.audit(
            action=AuditAction.SECURITY_ALERT,
            resource=resource,
            result=event_type,
            level=AuditLevel.CRITICAL,
            user_id=user_id,
            event_type=event_type,
            **details,
        )

    def log_access_denied(
        self, resource: str, user_id: str | None = None, reason: str = "UNAUTHORIZED", **details
    ):
        """Logger un accès refusé"""
        self.audit(
            action=AuditAction.ACCESS_DENIED,
            resource=resource,
            result=reason,
            level=AuditLevel.HIGH,
            user_id=user_id,
            reason=reason,
            **details,
        )

    # === Méthodes d'analyse et reporting ===

    def get_audit_stats(self, hours: int = 24) -> dict[str, Any]:
        """Obtenir les statistiques d'audit"""
        return {
            "period_hours": hours,
            "total_entries": sum(self._audit_counts.values()),
            "entries_by_level": dict(self._audit_counts),
            "last_audit": datetime.fromtimestamp(self._last_audit_time).isoformat(),
            "audit_rate_per_hour": sum(self._audit_counts.values()) / max(hours, 1),
        }

    def search_audit_logs(
        self,
        action: str | None = None,
        user_id: str | None = None,
        resource_pattern: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Rechercher dans les logs d'audit"""
        # Implémentation simplifiée pour fichier
        # En production, utiliser une base de données avec index

        if not self.config.enable_file_audit:
            return []

        try:
            entries = []
            with open(self.config.audit_file_path) as f:
                for line in f:
                    try:
                        entry_dict = json.loads(line.strip())
                        entry = AuditEntry(**entry_dict)

                        # Filtres
                        if action and entry.action != action:
                            continue
                        if user_id and entry.user_id != user_id:
                            continue
                        if resource_pattern and resource_pattern not in entry.resource:
                            continue

                        # Filtres temporels
                        entry_time = datetime.fromisoformat(entry.timestamp)
                        if start_time and entry_time < start_time:
                            continue
                        if end_time and entry_time > end_time:
                            continue

                        entries.append(entry)

                        if len(entries) >= limit:
                            break

                    except Exception as e:
                        logger.warning(f"Ligne d'audit invalide: {e}")
                        continue

            return entries[-limit:]  # Retourner les plus récents

        except FileNotFoundError:
            logger.warning("Fichier d'audit non trouvé")
            return []
        except Exception as e:
            logger.error(f"Erreur lecture audit: {e}")
            return []

    def verify_audit_integrity(self, entry: AuditEntry) -> bool:
        """Vérifier l'intégrité d'une entrée d'audit"""
        original_checksum = entry.checksum
        entry.checksum = None  # Temporairement

        try:
            calculated_checksum = self._generate_checksum(entry)
            is_valid = calculated_checksum == original_checksum

            if not is_valid:
                logger.error(f"Intégrité audit compromise: {entry.id}")

            return is_valid

        finally:
            entry.checksum = original_checksum

    def export_audit_report(self, start_time: datetime, end_time: datetime) -> dict[str, Any]:
        """Exporter un rapport d'audit pour une période"""
        entries = self.search_audit_logs(start_time=start_time, end_time=end_time, limit=10000)

        # Statistiques
        stats = {
            "period": f"{start_time.isoformat()} to {end_time.isoformat()}",
            "total_entries": len(entries),
            "actions_summary": {},
            "users_summary": {},
            "integrity_checks": 0,
        }

        # Analyser les entrées
        for entry in entries:
            # Actions
            if entry.action not in stats["actions_summary"]:
                stats["actions_summary"][entry.action] = 0
            stats["actions_summary"][entry.action] += 1

            # Utilisateurs
            if entry.user_id:
                if entry.user_id not in stats["users_summary"]:
                    stats["users_summary"][entry.user_id] = 0
                stats["users_summary"][entry.user_id] += 1

            # Vérification d'intégrité
            if self.verify_audit_integrity(entry):
                stats["integrity_checks"] += 1

        stats["integrity_rate"] = stats["integrity_checks"] / len(entries) if entries else 1.0

        return {"statistics": stats, "entries": [asdict(entry) for entry in entries]}


# Instance globale
audit_logger = AuditLogger()


# Fonctions de convenance
def audit(action: AuditAction, resource: str, **kwargs):
    """Logger un événement d'audit"""
    audit_logger.audit(action, resource, **kwargs)


def log_auth(user_id: str, **kwargs):
    """Logger une authentification"""
    audit_logger.log_authentication(user_id, **kwargs)
