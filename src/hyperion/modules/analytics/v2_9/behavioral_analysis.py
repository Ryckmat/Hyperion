"""
Hyperion v2.9 - Behavioral Analysis
Analyse comportementale avancée des utilisateurs
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """Types de comportements"""

    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    ANOMALOUS = "anomalous"
    MALICIOUS = "malicious"


class ActionType(Enum):
    """Types d'actions utilisateur"""

    LOGIN = "login"
    LOGOUT = "logout"
    SEARCH = "search"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    API_CALL = "api_call"
    ADMIN_ACTION = "admin_action"
    DATA_ACCESS = "data_access"


@dataclass
class UserAction:
    """Action utilisateur"""

    user_id: str
    action_type: ActionType
    timestamp: float
    resource: str
    metadata: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class BehaviorPattern:
    """Pattern comportemental détecté"""

    pattern_id: str
    user_id: str
    behavior_type: BehaviorType
    confidence: float
    description: str
    evidence: list[UserAction]
    first_occurrence: float
    last_occurrence: float
    frequency: int = 1


@dataclass
class UserProfile:
    """Profil comportemental d'un utilisateur"""

    user_id: str
    creation_time: float
    last_activity: float
    action_counts: dict[ActionType, int] = field(default_factory=lambda: defaultdict(int))
    resource_access: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    time_patterns: dict[int, int] = field(
        default_factory=lambda: defaultdict(int)
    )  # heure -> count
    ip_addresses: set[str] = field(default_factory=set)
    user_agents: set[str] = field(default_factory=set)
    baseline_established: bool = False


class BehavioralAnalyzer:
    """Analyseur comportemental avancé"""

    def __init__(
        self,
        baseline_period_hours: int = 24,
        anomaly_threshold: float = 0.8,
        max_user_profiles: int = 10000,
    ):

        self.baseline_period_hours = baseline_period_hours
        self.anomaly_threshold = anomaly_threshold
        self.max_user_profiles = max_user_profiles

        # Storage
        self.user_profiles: dict[str, UserProfile] = {}
        self.user_actions: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.detected_patterns: list[BehaviorPattern] = []

        # Configuration des règles d'analyse
        self.setup_analysis_rules()

        logger.info("BehavioralAnalyzer initialisé")

    def setup_analysis_rules(self):
        """Configuration des règles d'analyse comportementale"""
        self.suspicious_rules = [
            self.check_login_anomalies,
            self.check_data_access_patterns,
            self.check_time_based_anomalies,
            self.check_resource_abuse,
            self.check_admin_escalation,
        ]

        self.anomaly_rules = [
            self.check_volume_anomalies,
            self.check_geographical_anomalies,
            self.check_device_anomalies,
            self.check_sequence_anomalies,
        ]

    def record_user_action(self, action: UserAction):
        """Enregistre une action utilisateur"""
        user_id = action.user_id

        # Créer ou mettre à jour le profil utilisateur
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id, creation_time=action.timestamp, last_activity=action.timestamp
            )

        profile = self.user_profiles[user_id]
        profile.last_activity = action.timestamp
        profile.action_counts[action.action_type] += 1
        profile.resource_access[action.resource] += 1

        # Patterns temporels
        hour = int((action.timestamp % (24 * 3600)) // 3600)
        profile.time_patterns[hour] += 1

        # Métadonnées de sécurité
        if action.ip_address:
            profile.ip_addresses.add(action.ip_address)
        if action.user_agent:
            profile.user_agents.add(action.user_agent)

        # Stocker l'action
        self.user_actions[user_id].append(action)

        # Établir baseline après période d'observation
        if not profile.baseline_established:
            observation_time = action.timestamp - profile.creation_time
            if observation_time > self.baseline_period_hours * 3600:
                profile.baseline_established = True
                logger.info(f"Baseline établi pour utilisateur {user_id}")

        # Analyser en temps réel si baseline établi
        if profile.baseline_established:
            self._analyze_user_behavior(user_id, action)

    def _analyze_user_behavior(self, user_id: str, latest_action: UserAction):
        """Analyse le comportement d'un utilisateur"""
        try:
            # Analyser les patterns suspects
            for rule in self.suspicious_rules:
                pattern = rule(user_id, latest_action)
                if pattern and pattern.confidence >= self.anomaly_threshold:
                    self.detected_patterns.append(pattern)
                    logger.warning(f"Pattern suspect détecté: {pattern.description} pour {user_id}")

            # Analyser les anomalies
            for rule in self.anomaly_rules:
                pattern = rule(user_id, latest_action)
                if pattern and pattern.confidence >= self.anomaly_threshold:
                    self.detected_patterns.append(pattern)
                    logger.warning(f"Anomalie détectée: {pattern.description} pour {user_id}")

        except Exception as e:
            logger.error(f"Erreur analyse comportementale pour {user_id}: {e}")

    def check_login_anomalies(self, user_id: str, action: UserAction) -> BehaviorPattern | None:
        """Détecte les anomalies de connexion"""
        if action.action_type != ActionType.LOGIN:
            return None

        profile = self.user_profiles[user_id]
        recent_logins = [
            a
            for a in self.user_actions[user_id]
            if a.action_type == ActionType.LOGIN and a.timestamp > time.time() - 3600
        ]

        # Trop de tentatives de connexion
        if len(recent_logins) > 10:
            return BehaviorPattern(
                pattern_id=f"login_spam_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.SUSPICIOUS,
                confidence=0.9,
                description=f"Nombre anormal de connexions: {len(recent_logins)} en 1 heure",
                evidence=recent_logins,
                first_occurrence=recent_logins[0].timestamp,
                last_occurrence=action.timestamp,
                frequency=len(recent_logins),
            )

        # Connexion depuis nouvelle IP
        if action.ip_address and len(profile.ip_addresses) > 1:
            known_ips = {a.ip_address for a in self.user_actions[user_id][:-1] if a.ip_address}
            if action.ip_address not in known_ips:
                return BehaviorPattern(
                    pattern_id=f"new_ip_{user_id}_{int(time.time())}",
                    user_id=user_id,
                    behavior_type=BehaviorType.SUSPICIOUS,
                    confidence=0.7,
                    description=f"Connexion depuis nouvelle IP: {action.ip_address}",
                    evidence=[action],
                    first_occurrence=action.timestamp,
                    last_occurrence=action.timestamp,
                )

        return None

    def check_data_access_patterns(
        self, user_id: str, action: UserAction
    ) -> BehaviorPattern | None:
        """Détecte les patterns d'accès aux données suspects"""
        if action.action_type not in [ActionType.DATA_ACCESS, ActionType.DOWNLOAD]:
            return None

        # Get recent data access actions for analysis
        recent_data_access = [
            a
            for a in self.user_actions[user_id]
            if a.action_type in [ActionType.DATA_ACCESS, ActionType.DOWNLOAD]
            and a.timestamp > time.time() - 1800  # 30 minutes
        ]

        # Accès massif aux données
        if len(recent_data_access) > 50:
            return BehaviorPattern(
                pattern_id=f"data_exfiltration_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.SUSPICIOUS,
                confidence=0.85,
                description=f"Accès massif aux données: {len(recent_data_access)} en 30 minutes",
                evidence=recent_data_access,
                first_occurrence=recent_data_access[0].timestamp,
                last_occurrence=action.timestamp,
                frequency=len(recent_data_access),
            )

        return None

    def check_time_based_anomalies(
        self, user_id: str, action: UserAction
    ) -> BehaviorPattern | None:
        """Détecte les anomalies temporelles"""
        profile = self.user_profiles[user_id]
        current_hour = int((action.timestamp % (24 * 3600)) // 3600)

        # Calculer les heures d'activité normales
        total_actions = sum(profile.time_patterns.values())
        if total_actions < 50:  # Pas assez de données
            return None

        # Heures inhabituelles (moins de 1% de l'activité habituelle)
        normal_activity = profile.time_patterns.get(current_hour, 0) / total_actions
        if normal_activity < 0.01 and total_actions > 100:
            return BehaviorPattern(
                pattern_id=f"unusual_time_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.ANOMALOUS,
                confidence=0.8,
                description=f"Activité à heure inhabituelle: {current_hour}h",
                evidence=[action],
                first_occurrence=action.timestamp,
                last_occurrence=action.timestamp,
            )

        return None

    def check_resource_abuse(self, user_id: str, action: UserAction) -> BehaviorPattern | None:
        """Détecte l'abus de ressources"""
        profile = self.user_profiles[user_id]

        # Calcul de l'utilisation normale de cette ressource
        resource_usage = profile.resource_access.get(action.resource, 0)
        total_usage = sum(profile.resource_access.values())

        if total_usage < 20:  # Pas assez de données
            return None

        usage_ratio = resource_usage / total_usage

        # Si plus de 50% de l'activité sur une seule ressource
        if usage_ratio > 0.5 and resource_usage > 100:
            return BehaviorPattern(
                pattern_id=f"resource_abuse_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.SUSPICIOUS,
                confidence=0.75,
                description=f"Abus de ressource {action.resource}: {resource_usage} accès ({usage_ratio:.1%})",
                evidence=[action],
                first_occurrence=action.timestamp,
                last_occurrence=action.timestamp,
            )

        return None

    def check_admin_escalation(self, user_id: str, action: UserAction) -> BehaviorPattern | None:
        """Détecte les tentatives d'escalade administrative"""
        if action.action_type != ActionType.ADMIN_ACTION:
            return None

        # Vérifier l'historique des actions admin
        admin_actions = [
            a for a in self.user_actions[user_id] if a.action_type == ActionType.ADMIN_ACTION
        ]

        # Premier accès admin suspect
        if len(admin_actions) == 1:  # Première action admin
            return BehaviorPattern(
                pattern_id=f"admin_escalation_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.SUSPICIOUS,
                confidence=0.8,
                description="Première action administrative détectée",
                evidence=[action],
                first_occurrence=action.timestamp,
                last_occurrence=action.timestamp,
            )

        return None

    def check_volume_anomalies(self, user_id: str, action: UserAction) -> BehaviorPattern | None:
        """Détecte les anomalies de volume"""
        recent_actions = [
            a for a in self.user_actions[user_id] if a.timestamp > time.time() - 300  # 5 minutes
        ]

        # Volume anormalement élevé
        if len(recent_actions) > 100:
            return BehaviorPattern(
                pattern_id=f"volume_anomaly_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.ANOMALOUS,
                confidence=0.9,
                description=f"Volume d'actions anormal: {len(recent_actions)} en 5 minutes",
                evidence=recent_actions,
                first_occurrence=recent_actions[0].timestamp,
                last_occurrence=action.timestamp,
                frequency=len(recent_actions),
            )

        return None

    def check_geographical_anomalies(
        self, user_id: str, action: UserAction
    ) -> BehaviorPattern | None:
        """Détecte les anomalies géographiques"""
        if not action.ip_address:
            return None

        profile = self.user_profiles[user_id]

        # Simulation de détection géographique simple
        if len(profile.ip_addresses) > 5:  # Trop d'IPs différentes
            return BehaviorPattern(
                pattern_id=f"geo_anomaly_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.ANOMALOUS,
                confidence=0.7,
                description=f"Utilisation de multiples IP: {len(profile.ip_addresses)}",
                evidence=[action],
                first_occurrence=action.timestamp,
                last_occurrence=action.timestamp,
            )

        return None

    def check_device_anomalies(self, user_id: str, action: UserAction) -> BehaviorPattern | None:
        """Détecte les anomalies de device"""
        if not action.user_agent:
            return None

        profile = self.user_profiles[user_id]

        # Trop de user agents différents
        if len(profile.user_agents) > 3:
            return BehaviorPattern(
                pattern_id=f"device_anomaly_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.ANOMALOUS,
                confidence=0.6,
                description=f"Utilisation de multiples devices: {len(profile.user_agents)}",
                evidence=[action],
                first_occurrence=action.timestamp,
                last_occurrence=action.timestamp,
            )

        return None

    def check_sequence_anomalies(self, user_id: str, action: UserAction) -> BehaviorPattern | None:
        """Détecte les séquences d'actions anormales"""
        recent_actions = list(self.user_actions[user_id])[-10:]  # 10 dernières actions

        if len(recent_actions) < 5:
            return None

        # Séquence répétitive suspecte
        action_sequence = [a.action_type for a in recent_actions]
        unique_actions = set(action_sequence)

        # Trop répétitif (moins de 3 types d'actions différentes)
        if len(unique_actions) <= 2 and len(recent_actions) >= 10:
            return BehaviorPattern(
                pattern_id=f"sequence_anomaly_{user_id}_{int(time.time())}",
                user_id=user_id,
                behavior_type=BehaviorType.ANOMALOUS,
                confidence=0.7,
                description=f"Séquence d'actions répétitive: {list(unique_actions)}",
                evidence=recent_actions,
                first_occurrence=recent_actions[0].timestamp,
                last_occurrence=action.timestamp,
                frequency=len(recent_actions),
            )

        return None

    def get_user_behavior_summary(self, user_id: str) -> dict[str, Any] | None:
        """Résumé comportemental d'un utilisateur"""
        if user_id not in self.user_profiles:
            return None

        profile = self.user_profiles[user_id]
        recent_patterns = [
            p
            for p in self.detected_patterns
            if p.user_id == user_id and p.last_occurrence > time.time() - 86400
        ]

        return {
            "user_id": user_id,
            "profile_created": profile.creation_time,
            "last_activity": profile.last_activity,
            "baseline_established": profile.baseline_established,
            "total_actions": sum(profile.action_counts.values()),
            "action_distribution": dict(profile.action_counts),
            "unique_resources": len(profile.resource_access),
            "unique_ips": len(profile.ip_addresses),
            "unique_devices": len(profile.user_agents),
            "recent_patterns": len(recent_patterns),
            "risk_score": self._calculate_risk_score(user_id),
        }

    def _calculate_risk_score(self, user_id: str) -> float:
        """Calcule un score de risque pour l'utilisateur"""
        recent_patterns = [
            p
            for p in self.detected_patterns
            if p.user_id == user_id and p.last_occurrence > time.time() - 86400
        ]

        if not recent_patterns:
            return 0.0

        # Score basé sur les patterns récents
        risk_score = 0.0
        for pattern in recent_patterns:
            if pattern.behavior_type == BehaviorType.MALICIOUS:
                risk_score += pattern.confidence * 1.0
            elif pattern.behavior_type == BehaviorType.SUSPICIOUS:
                risk_score += pattern.confidence * 0.8
            elif pattern.behavior_type == BehaviorType.ANOMALOUS:
                risk_score += pattern.confidence * 0.6

        return min(1.0, risk_score)

    def get_high_risk_users(self, risk_threshold: float = 0.7) -> list[dict[str, Any]]:
        """Retourne les utilisateurs à haut risque"""
        high_risk_users = []

        for user_id in self.user_profiles:
            risk_score = self._calculate_risk_score(user_id)
            if risk_score >= risk_threshold:
                summary = self.get_user_behavior_summary(user_id)
                summary["risk_score"] = risk_score
                high_risk_users.append(summary)

        # Trier par score de risque décroissant
        high_risk_users.sort(key=lambda x: x["risk_score"], reverse=True)

        return high_risk_users

    def get_behavior_statistics(self) -> dict[str, Any]:
        """Statistiques générales du comportement"""
        total_users = len(self.user_profiles)
        active_users = len(
            [p for p in self.user_profiles.values() if p.last_activity > time.time() - 86400]
        )

        recent_patterns = [
            p for p in self.detected_patterns if p.last_occurrence > time.time() - 86400
        ]

        pattern_counts = defaultdict(int)
        for pattern in recent_patterns:
            pattern_counts[pattern.behavior_type] += 1

        return {
            "total_users": total_users,
            "active_users_24h": active_users,
            "patterns_detected_24h": len(recent_patterns),
            "pattern_breakdown": dict(pattern_counts),
            "high_risk_users": len(self.get_high_risk_users()),
            "average_actions_per_user": sum(
                sum(p.action_counts.values()) for p in self.user_profiles.values()
            )
            / max(total_users, 1),
        }


# Instance globale
default_behavioral_analyzer = BehavioralAnalyzer()
