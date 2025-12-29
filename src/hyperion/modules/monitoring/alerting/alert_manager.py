"""
Alert Manager for Hyperion v3.0

Système d'alerting intelligent avec escalade et intégrations multiples.
"""

import hashlib
import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Sévérité des alertes"""

    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    FATAL = 5


class AlertStatus(Enum):
    """Statut des alertes"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertCategory(Enum):
    """Catégories d'alertes Hyperion"""

    # Performance
    PERFORMANCE = "performance"
    LATENCY = "latency"
    THROUGHPUT = "throughput"

    # Ressources système
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"

    # Services
    API = "api"
    DATABASE = "database"
    RAG = "rag"
    ML = "ml"

    # Qualité
    QUALITY = "quality"
    HALLUCINATION = "hallucination"
    ACCURACY = "accuracy"

    # Sécurité
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"

    # Système
    HEALTH = "health"
    AVAILABILITY = "availability"


@dataclass
class Alert:
    """Alerte structurée"""

    id: str
    title: str
    message: str
    severity: AlertSeverity
    category: AlertCategory
    source: str
    timestamp: float
    status: AlertStatus = AlertStatus.ACTIVE

    # Métadonnées
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, Any] = field(default_factory=dict)

    # Gestion escalade
    escalation_level: int = 0
    acknowledged_by: str | None = None
    acknowledged_at: float | None = None
    resolved_at: float | None = None

    # Groupement
    fingerprint: str | None = None
    group_key: str | None = None


@dataclass
class AlertRule:
    """Règle d'alerte"""

    name: str
    query: str  # Expression de la condition
    severity: AlertSeverity
    category: AlertCategory
    threshold: float
    duration: int  # Durée en secondes avant déclenchement

    # Configuration
    enabled: bool = True
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    # Contrôle fréquence
    evaluation_interval: int = 60  # Secondes
    last_evaluation: float = 0

    # État
    firing: bool = False
    firing_since: float | None = None


@dataclass
class NotificationChannel:
    """Canal de notification"""

    name: str
    type: str  # email, slack, webhook, sms
    config: dict[str, Any]
    enabled: bool = True

    # Filtres
    severity_filter: list[AlertSeverity] | None = None
    category_filter: list[AlertCategory] | None = None

    # Rate limiting
    rate_limit: int | None = None  # Max notifications par heure
    last_sent: float = 0
    sent_count_hour: int = 0


class AlertManager:
    """
    Gestionnaire d'alertes enterprise pour Hyperion v3.0

    Fonctionnalités :
    - Règles d'alerting configurables
    - Groupement et déduplication intelligents
    - Escalade automatique
    - Intégrations multiples (email, Slack, webhooks)
    - Suppression temporaire
    - Métriques et analytics d'alerting
    - Dashboard temps réel
    """

    def __init__(
        self,
        max_alerts: int = 10000,
        default_evaluation_interval: int = 60,
        enable_auto_resolution: bool = True,
    ):

        self.max_alerts = max_alerts
        self.default_evaluation_interval = default_evaluation_interval
        self.enable_auto_resolution = enable_auto_resolution

        # Storage
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=max_alerts)
        self.alert_rules: dict[str, AlertRule] = {}
        self.notification_channels: dict[str, NotificationChannel] = {}

        # Groupement et déduplication
        self.alert_groups: dict[str, list[str]] = defaultdict(list)
        self.suppression_rules: list[dict] = []

        # Métriques
        self.alert_metrics = {
            "total_fired": 0,
            "total_resolved": 0,
            "by_severity": {s.name: 0 for s in AlertSeverity},
            "by_category": {c.name: 0 for c in AlertCategory},
        }

        # Threading
        self._lock = threading.Lock()
        self._evaluator_thread = None
        self._running = False

        # Callbacks personnalisés
        self._alert_callbacks: list[Callable] = []

        logger.info("AlertManager initialisé")

    def start(self):
        """Démarrer le gestionnaire d'alertes"""
        if self._running:
            return

        self._running = True
        self._evaluator_thread = threading.Thread(target=self._evaluation_loop, daemon=True)
        self._evaluator_thread.start()
        logger.info("AlertManager démarré")

    def stop(self):
        """Arrêter le gestionnaire d'alertes"""
        self._running = False
        if self._evaluator_thread:
            self._evaluator_thread.join(timeout=5.0)
        logger.info("AlertManager arrêté")

    def _evaluation_loop(self):
        """Boucle d'évaluation des règles"""
        while self._running:
            try:
                self._evaluate_rules()
                self._check_auto_resolution()
                self._cleanup_old_alerts()
                time.sleep(self.default_evaluation_interval)
            except Exception as e:
                logger.error(f"Erreur évaluation alertes: {e}")
                time.sleep(10)  # Attendre avant retry

    def add_rule(self, rule: AlertRule):
        """Ajouter une règle d'alerte"""
        with self._lock:
            self.alert_rules[rule.name] = rule
        logger.info(f"Règle d'alerte ajoutée: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Supprimer une règle d'alerte"""
        with self._lock:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                logger.info(f"Règle d'alerte supprimée: {rule_name}")

    def add_notification_channel(self, channel: NotificationChannel):
        """Ajouter un canal de notification"""
        with self._lock:
            self.notification_channels[channel.name] = channel
        logger.info(f"Canal de notification ajouté: {channel.name}")

    def fire_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        category: AlertCategory,
        source: str,
        **kwargs,
    ) -> str:
        """Déclencher une alerte manuellement"""

        # Créer l'alerte
        alert_id = self._generate_alert_id(title, source)
        fingerprint = self._generate_fingerprint(title, source, severity)

        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            category=category,
            source=source,
            timestamp=time.time(),
            fingerprint=fingerprint,
            **kwargs,
        )

        return self._process_alert(alert)

    def _process_alert(self, alert: Alert) -> str:
        """Traiter une nouvelle alerte"""
        with self._lock:
            # Vérifier suppression
            if self._is_suppressed(alert):
                logger.debug(f"Alerte supprimée: {alert.title}")
                return alert.id

            # Déduplication
            existing_alert = self._find_duplicate(alert)
            if existing_alert:
                self._update_existing_alert(existing_alert, alert)
                return existing_alert.id

            # Ajouter nouvelle alerte
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)

            # Groupement
            group_key = self._generate_group_key(alert)
            alert.group_key = group_key
            self.alert_groups[group_key].append(alert.id)

            # Métriques
            self.alert_metrics["total_fired"] += 1
            self.alert_metrics["by_severity"][alert.severity.name] += 1
            self.alert_metrics["by_category"][alert.category.name] += 1

            logger.warning(f"ALERTE: {alert.severity.name} - {alert.title}")

        # Notifications (hors lock)
        self._send_notifications(alert)

        # Callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erreur callback alerte: {e}")

        return alert.id

    def _generate_alert_id(self, title: str, source: str) -> str:
        """Générer un ID unique pour l'alerte"""
        timestamp = str(int(time.time() * 1000))
        content = f"{title}_{source}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_fingerprint(self, title: str, source: str, severity: AlertSeverity) -> str:
        """Générer une empreinte pour déduplication"""
        content = f"{title}_{source}_{severity.name}"
        return hashlib.md5(content.encode()).hexdigest()

    def _generate_group_key(self, alert: Alert) -> str:
        """Générer une clé de groupement"""
        return f"{alert.category.name}_{alert.source}_{alert.severity.name}"

    def _find_duplicate(self, alert: Alert) -> Alert | None:
        """Trouver une alerte dupliquée"""
        for existing in self.active_alerts.values():
            if existing.fingerprint == alert.fingerprint and existing.status == AlertStatus.ACTIVE:
                return existing
        return None

    def _update_existing_alert(self, existing: Alert, new_alert: Alert):
        """Mettre à jour une alerte existante"""
        existing.timestamp = new_alert.timestamp
        existing.message = new_alert.message
        # Pas d'escalade pour les duplicatas simples

    def _is_suppressed(self, alert: Alert) -> bool:
        """Vérifier si l'alerte est supprimée"""
        return any(self._matches_suppression_rule(alert, rule) for rule in self.suppression_rules)

    def _matches_suppression_rule(self, alert: Alert, rule: dict) -> bool:
        """Vérifier si l'alerte correspond à une règle de suppression"""
        # Implémentation simple - extensible
        if "category" in rule and alert.category.name not in rule["category"]:
            return False
        if "severity" in rule and alert.severity.name not in rule["severity"]:
            return False
        return not ("source" in rule and alert.source not in rule["source"])

    def _evaluate_rules(self):
        """Évaluer toutes les règles d'alerte"""
        current_time = time.time()

        with self._lock:
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue

                if current_time - rule.last_evaluation < rule.evaluation_interval:
                    continue

                try:
                    self._evaluate_single_rule(rule, current_time)
                except Exception as e:
                    logger.error(f"Erreur évaluation règle {rule.name}: {e}")

                rule.last_evaluation = current_time

    def _evaluate_single_rule(self, rule: AlertRule, current_time: float):
        """Évaluer une règle spécifique"""
        # Simulation d'évaluation - à remplacer par vraie logique
        # En production, intégrer avec métriques Prometheus/monitoring

        # Exemple d'évaluation basique
        metric_value = self._get_metric_value(rule.query)

        if metric_value is None:
            return

        threshold_exceeded = self._check_threshold(metric_value, rule.threshold, rule.query)

        if threshold_exceeded and not rule.firing:
            # Démarrer période d'observation
            if rule.firing_since is None:
                rule.firing_since = current_time
            elif current_time - rule.firing_since >= rule.duration:
                # Seuil dépassé suffisamment longtemps
                self._fire_rule_alert(rule, metric_value)
                rule.firing = True

        elif not threshold_exceeded and rule.firing:
            # Résoudre l'alerte
            self._resolve_rule_alert(rule)
            rule.firing = False
            rule.firing_since = None

        elif not threshold_exceeded:
            # Reset période d'observation
            rule.firing_since = None

    def _get_metric_value(self, _query: str) -> float | None:
        """Obtenir la valeur d'une métrique (stub)"""
        # TODO: Intégrer avec système de métriques real
        # Pour l'instant, simuler avec des valeurs
        import random

        return random.uniform(0, 100)

    def _check_threshold(self, value: float, threshold: float, _query: str) -> bool:
        """Vérifier si le seuil est dépassé"""
        # Logique simple - extensible selon le type de métrique
        return value > threshold

    def _fire_rule_alert(self, rule: AlertRule, metric_value: float):
        """Déclencher une alerte pour une règle"""
        title = f"Rule Alert: {rule.name}"
        message = f"Metric {rule.query} = {metric_value:.2f} (threshold: {rule.threshold})"

        self.fire_alert(
            title=title,
            message=message,
            severity=rule.severity,
            category=rule.category,
            source=f"rule:{rule.name}",
            labels=rule.labels,
            annotations={
                **rule.annotations,
                "metric_value": metric_value,
                "threshold": rule.threshold,
                "query": rule.query,
            },
        )

    def _resolve_rule_alert(self, rule: AlertRule):
        """Résoudre une alerte de règle"""
        # Chercher l'alerte active correspondante
        for alert_id, alert in self.active_alerts.items():
            if alert.source == f"rule:{rule.name}" and alert.status == AlertStatus.ACTIVE:
                self.resolve_alert(alert_id, "Auto-resolved: threshold no longer exceeded")
                break

    def _send_notifications(self, alert: Alert):
        """Envoyer les notifications pour une alerte"""
        current_time = time.time()

        for channel in self.notification_channels.values():
            if not channel.enabled:
                continue

            # Filtres
            if channel.severity_filter and alert.severity not in channel.severity_filter:
                continue

            if channel.category_filter and alert.category not in channel.category_filter:
                continue

            # Rate limiting
            if channel.rate_limit:
                hours_since_reset = (current_time - channel.last_sent) / 3600
                if hours_since_reset >= 1:
                    channel.sent_count_hour = 0

                if channel.sent_count_hour >= channel.rate_limit:
                    continue

            # Envoyer notification
            try:
                self._send_notification_to_channel(alert, channel)
                channel.last_sent = current_time
                channel.sent_count_hour += 1
                logger.info(f"Notification envoyée: {channel.name}")
            except Exception as e:
                logger.error(f"Erreur notification {channel.name}: {e}")

    def _send_notification_to_channel(self, alert: Alert, channel: NotificationChannel):
        """Envoyer notification à un canal spécifique"""
        # Formatage du message
        notification_text = self._format_notification(alert, channel)

        if channel.type == "email":
            self._send_email(notification_text, channel.config)
        elif channel.type == "slack":
            self._send_slack(notification_text, channel.config)
        elif channel.type == "webhook":
            self._send_webhook(alert, channel.config)
        else:
            logger.warning(f"Type de canal non supporté: {channel.type}")

    def _format_notification(self, alert: Alert, _channel: NotificationChannel) -> str:
        """Formater le message de notification"""
        timestamp = datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S")

        return f"""
🚨 HYPERION ALERT - {alert.severity.name}

Title: {alert.title}
Category: {alert.category.name}
Source: {alert.source}
Time: {timestamp}

{alert.message}

Alert ID: {alert.id}
        """.strip()

    def _send_email(self, text: str, _config: dict):
        """Envoyer email (stub)"""
        logger.info(f"EMAIL: {text[:50]}...")

    def _send_slack(self, text: str, _config: dict):
        """Envoyer message Slack (stub)"""
        logger.info(f"SLACK: {text[:50]}...")

    def _send_webhook(self, alert: Alert, _config: dict):
        """Envoyer webhook (stub)"""
        {"alert": asdict(alert), "timestamp": time.time()}
        logger.info(f"WEBHOOK: Alert {alert.id}")

    def acknowledge_alert(self, alert_id: str, user: str, comment: str = "") -> bool:
        """Acquitter une alerte"""
        with self._lock:
            if alert_id not in self.active_alerts:
                return False

            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user
            alert.acknowledged_at = time.time()

            if comment:
                alert.annotations["ack_comment"] = comment

            logger.info(f"Alerte acquittée: {alert_id} par {user}")
            return True

    def resolve_alert(self, alert_id: str, comment: str = "") -> bool:
        """Résoudre une alerte"""
        with self._lock:
            if alert_id not in self.active_alerts:
                return False

            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = time.time()

            if comment:
                alert.annotations["resolution_comment"] = comment

            # Retirer des alertes actives
            del self.active_alerts[alert_id]

            # Métriques
            self.alert_metrics["total_resolved"] += 1

            logger.info(f"Alerte résolue: {alert_id}")
            return True

    def _check_auto_resolution(self):
        """Vérifier les résolutions automatiques"""
        if not self.enable_auto_resolution:
            return

        current_time = time.time()
        auto_resolve_timeout = 3600  # 1 heure

        to_resolve = []

        with self._lock:
            for alert_id, alert in self.active_alerts.items():
                if (
                    alert.status == AlertStatus.ACTIVE
                    and current_time - alert.timestamp > auto_resolve_timeout
                ):
                    to_resolve.append(alert_id)

        for alert_id in to_resolve:
            self.resolve_alert(alert_id, "Auto-resolved: timeout")

    def _cleanup_old_alerts(self):
        """Nettoyer les anciennes alertes"""
        cutoff_time = time.time() - (7 * 24 * 3600)  # 7 jours

        # Nettoyer l'historique
        while self.alert_history and self.alert_history[0].timestamp < cutoff_time:
            self.alert_history.popleft()

    def add_callback(self, callback: Callable[[Alert], None]):
        """Ajouter un callback pour nouvelles alertes"""
        self._alert_callbacks.append(callback)

    def get_active_alerts(
        self, severity: AlertSeverity | None = None, category: AlertCategory | None = None
    ) -> list[Alert]:
        """Obtenir les alertes actives"""
        with self._lock:
            alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if category:
            alerts = [a for a in alerts if a.category == category]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def get_alert_statistics(self) -> dict[str, Any]:
        """Obtenir les statistiques d'alerting"""
        with self._lock:
            active_count = len(self.active_alerts)

            return {
                "active_alerts": active_count,
                "total_fired": self.alert_metrics["total_fired"],
                "total_resolved": self.alert_metrics["total_resolved"],
                "by_severity": dict(self.alert_metrics["by_severity"]),
                "by_category": dict(self.alert_metrics["by_category"]),
                "rules_count": len(self.alert_rules),
                "channels_count": len(self.notification_channels),
            }

    def export_config(self) -> dict[str, Any]:
        """Exporter la configuration complète"""
        with self._lock:
            return {
                "rules": [asdict(rule) for rule in self.alert_rules.values()],
                "channels": [asdict(ch) for ch in self.notification_channels.values()],
                "suppression_rules": list(self.suppression_rules),
                "settings": {
                    "max_alerts": self.max_alerts,
                    "evaluation_interval": self.default_evaluation_interval,
                    "auto_resolution": self.enable_auto_resolution,
                },
            }


# Instance globale
alert_manager = AlertManager()


# Fonctions de convenance
def fire_alert(
    title: str,
    message: str,
    severity: AlertSeverity,
    category: AlertCategory,
    source: str,
    **kwargs,
) -> str:
    """Déclencher une alerte"""
    return alert_manager.fire_alert(title, message, severity, category, source, **kwargs)


def add_rule(
    name: str,
    query: str,
    severity: AlertSeverity,
    category: AlertCategory,
    threshold: float,
    **kwargs,
):
    """Ajouter une règle d'alerte"""
    rule = AlertRule(
        name=name, query=query, severity=severity, category=category, threshold=threshold, **kwargs
    )
    alert_manager.add_rule(rule)
