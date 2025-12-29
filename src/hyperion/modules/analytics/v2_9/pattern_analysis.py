"""
Hyperion v2.9 - Pattern Analysis
Analyse de patterns avancée pour le moteur d'intelligence
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types de patterns détectés"""

    TEMPORAL = "temporal"  # Patterns temporels
    BEHAVIORAL = "behavioral"  # Patterns comportementaux
    ANOMALY = "anomaly"  # Anomalies
    CORRELATION = "correlation"  # Corrélations
    SEQUENCE = "sequence"  # Séquences d'événements
    CLUSTERING = "clustering"  # Groupes d'utilisateurs/événements


@dataclass
class DetectedPattern:
    """Pattern détecté"""

    pattern_id: str
    pattern_type: PatternType
    confidence: float
    description: str
    evidence: dict[str, Any]
    first_seen: datetime
    last_seen: datetime
    occurrences: int = 1
    significance: float = 0.0


@dataclass
class AnalysisConfig:
    """Configuration pour l'analyse de patterns"""

    enable_temporal_analysis: bool = True
    enable_behavioral_analysis: bool = True
    enable_anomaly_detection: bool = True
    enable_correlation_analysis: bool = True
    min_confidence_threshold: float = 0.7
    min_significance_threshold: float = 0.5
    temporal_window_minutes: int = 60
    max_patterns_to_track: int = 1000


class TemporalAnalyzer:
    """Analyseur de patterns temporels"""

    def __init__(self, window_minutes: int = 60):
        self.window_minutes = window_minutes
        self.event_timeline = deque()
        self.hourly_patterns = defaultdict(list)
        self.daily_patterns = defaultdict(list)

    def analyze_temporal_patterns(self, events: list[dict]) -> list[DetectedPattern]:
        """Analyse les patterns temporels dans les événements"""
        patterns = []

        # Nettoyer les anciens événements
        cutoff_time = time.time() - (self.window_minutes * 60)
        self.event_timeline = deque(
            [event for event in self.event_timeline if event["timestamp"] > cutoff_time]
        )

        # Ajouter nouveaux événements
        for event in events:
            self.event_timeline.append(event)

        # Détecter patterns horaires
        hourly_patterns = self._detect_hourly_patterns()
        patterns.extend(hourly_patterns)

        # Détecter patterns de pics
        spike_patterns = self._detect_spike_patterns()
        patterns.extend(spike_patterns)

        # Détecter patterns cycliques
        cyclic_patterns = self._detect_cyclic_patterns()
        patterns.extend(cyclic_patterns)

        return patterns

    def _detect_hourly_patterns(self) -> list[DetectedPattern]:
        """Détecte les patterns par heure"""
        patterns = []

        if len(self.event_timeline) < 10:
            return patterns

        # Grouper par heure
        hourly_counts = defaultdict(int)
        for event in self.event_timeline:
            hour = datetime.fromtimestamp(event["timestamp"]).hour
            hourly_counts[hour] += 1

        # Calculer moyenne et écart-type
        counts = list(hourly_counts.values())
        if not counts:
            return patterns

        mean_count = np.mean(counts)
        std_count = np.std(counts)

        # Détecter heures avec activité significativement différente
        for hour, count in hourly_counts.items():
            if count > mean_count + 2 * std_count:
                confidence = min(0.95, (count - mean_count) / (3 * std_count))
                patterns.append(
                    DetectedPattern(
                        pattern_id=f"peak_hour_{hour}",
                        pattern_type=PatternType.TEMPORAL,
                        confidence=confidence,
                        description=f"Pic d'activité à {hour}h ({count} événements)",
                        evidence={
                            "hour": hour,
                            "count": count,
                            "average": mean_count,
                            "deviation": count - mean_count,
                        },
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        significance=confidence,
                    )
                )

        return patterns

    def _detect_spike_patterns(self) -> list[DetectedPattern]:
        """Détecte les pics soudains d'activité"""
        patterns = []

        if len(self.event_timeline) < 20:
            return patterns

        # Analyser par tranches de 5 minutes
        time_buckets = defaultdict(int)
        for event in self.event_timeline:
            bucket = int(event["timestamp"] // 300) * 300  # Tranches de 5 min
            time_buckets[bucket] += 1

        # Détecter les pics
        sorted_buckets = sorted(time_buckets.items())
        for i, (timestamp, count) in enumerate(sorted_buckets[:-1]):
            next_count = sorted_buckets[i + 1][1]

            # Pic si augmentation > 300%
            if count > 0 and next_count > count * 3:
                confidence = min(0.9, (next_count - count) / count)
                patterns.append(
                    DetectedPattern(
                        pattern_id=f"spike_{timestamp}",
                        pattern_type=PatternType.TEMPORAL,
                        confidence=confidence,
                        description=f"Pic soudain: {count} → {next_count} événements",
                        evidence={
                            "timestamp": timestamp,
                            "before": count,
                            "after": next_count,
                            "increase_ratio": next_count / count if count > 0 else 0,
                        },
                        first_seen=datetime.fromtimestamp(timestamp),
                        last_seen=datetime.fromtimestamp(timestamp + 300),
                        significance=confidence,
                    )
                )

        return patterns

    def _detect_cyclic_patterns(self) -> list[DetectedPattern]:
        """Détecte les patterns cycliques"""
        patterns = []

        # Simple détection de cyclicité basée sur l'autocorrélation
        if len(self.event_timeline) < 50:
            return patterns

        # Créer série temporelle par minutes
        minute_counts = defaultdict(int)
        for event in self.event_timeline:
            minute = int(event["timestamp"] // 60) * 60
            minute_counts[minute] += 1

        if len(minute_counts) < 20:
            return patterns

        # Calculer autocorrélation simple
        counts_series = list(minute_counts.values())
        for lag in [5, 10, 15, 30]:  # Cycles de 5, 10, 15, 30 minutes
            if len(counts_series) > lag * 2:
                correlation = self._calculate_lag_correlation(counts_series, lag)
                if correlation > 0.7:
                    patterns.append(
                        DetectedPattern(
                            pattern_id=f"cycle_{lag}min",
                            pattern_type=PatternType.TEMPORAL,
                            confidence=correlation,
                            description=f"Cycle récurrent de {lag} minutes",
                            evidence={
                                "cycle_length_minutes": lag,
                                "correlation": correlation,
                                "data_points": len(counts_series),
                            },
                            first_seen=datetime.now() - timedelta(minutes=len(counts_series)),
                            last_seen=datetime.now(),
                            significance=correlation,
                        )
                    )

        return patterns

    def _calculate_lag_correlation(self, series: list[float], lag: int) -> float:
        """Calcule corrélation avec décalage"""
        if len(series) < lag * 2:
            return 0.0

        x = series[:-lag]
        y = series[lag:]

        if len(x) == 0 or np.std(x) == 0 or np.std(y) == 0:
            return 0.0

        return abs(np.corrcoef(x, y)[0, 1]) if not np.isnan(np.corrcoef(x, y)[0, 1]) else 0.0


class BehavioralAnalyzer:
    """Analyseur de patterns comportementaux"""

    def __init__(self):
        self.user_sessions = defaultdict(dict)
        self.action_sequences = defaultdict(list)
        self.user_profiles = defaultdict(dict)

    def analyze_behavioral_patterns(self, events: list[dict]) -> list[DetectedPattern]:
        """Analyse les patterns comportementaux"""
        patterns = []

        # Mettre à jour les profils utilisateurs
        self._update_user_profiles(events)

        # Détecter patterns de navigation
        navigation_patterns = self._detect_navigation_patterns()
        patterns.extend(navigation_patterns)

        # Détecter comportements anormaux
        anomaly_patterns = self._detect_behavioral_anomalies()
        patterns.extend(anomaly_patterns)

        # Détecter groupes d'utilisateurs similaires
        clustering_patterns = self._detect_user_clusters()
        patterns.extend(clustering_patterns)

        return patterns

    def _update_user_profiles(self, events: list[dict]):
        """Met à jour les profils utilisateurs"""
        for event in events:
            user_id = event.get("user_id")
            if not user_id:
                continue

            # Mettre à jour actions
            action = event.get("event_type", "unknown")
            if "actions" not in self.user_profiles[user_id]:
                self.user_profiles[user_id]["actions"] = defaultdict(int)
            self.user_profiles[user_id]["actions"][action] += 1

            # Mettre à jour séquences d'actions
            self.action_sequences[user_id].append(
                {"action": action, "timestamp": event["timestamp"]}
            )

            # Garder seulement les 100 dernières actions
            if len(self.action_sequences[user_id]) > 100:
                self.action_sequences[user_id] = self.action_sequences[user_id][-100:]

    def _detect_navigation_patterns(self) -> list[DetectedPattern]:
        """Détecte les patterns de navigation"""
        patterns = []

        for user_id, sequences in self.action_sequences.items():
            if len(sequences) < 5:
                continue

            # Détecter séquences répétitives
            recent_actions = [s["action"] for s in sequences[-10:]]

            # Chercher patterns de 3 actions consécutives
            for i in range(len(recent_actions) - 5):
                pattern_candidate = recent_actions[i : i + 3]
                pattern_str = " -> ".join(pattern_candidate)

                # Compter occurrences
                occurrences = 0
                for j in range(len(recent_actions) - 2):
                    if recent_actions[j : j + 3] == pattern_candidate:
                        occurrences += 1

                if occurrences >= 2:  # Pattern répété au moins 2 fois
                    confidence = min(0.8, occurrences / 3.0)
                    patterns.append(
                        DetectedPattern(
                            pattern_id=f"nav_pattern_{user_id}_{hash(pattern_str)}",
                            pattern_type=PatternType.BEHAVIORAL,
                            confidence=confidence,
                            description=f"Pattern de navigation répétitif: {pattern_str}",
                            evidence={
                                "user_id": user_id,
                                "pattern": pattern_candidate,
                                "occurrences": occurrences,
                                "sequence_length": len(sequences),
                            },
                            first_seen=datetime.now(),
                            last_seen=datetime.now(),
                            occurrences=occurrences,
                            significance=confidence,
                        )
                    )

        return patterns

    def _detect_behavioral_anomalies(self) -> list[DetectedPattern]:
        """Détecte les comportements anormaux"""
        patterns = []

        for user_id, profile in self.user_profiles.items():
            actions = profile.get("actions", {})
            if not actions:
                continue

            # Calculer distribution normale des actions
            action_counts = list(actions.values())
            if len(action_counts) < 3:
                continue

            mean_actions = np.mean(action_counts)
            std_actions = np.std(action_counts)

            if std_actions == 0:
                continue

            # Détecter actions anormalement fréquentes
            for action, count in actions.items():
                z_score = abs((count - mean_actions) / std_actions)

                if z_score > 2.0:  # Plus de 2 écarts-types
                    confidence = min(0.9, z_score / 3.0)
                    patterns.append(
                        DetectedPattern(
                            pattern_id=f"anomaly_{user_id}_{action}",
                            pattern_type=PatternType.ANOMALY,
                            confidence=confidence,
                            description=f"Comportement anormal: {action} ({count} fois)",
                            evidence={
                                "user_id": user_id,
                                "action": action,
                                "count": count,
                                "z_score": z_score,
                                "mean": mean_actions,
                                "std": std_actions,
                            },
                            first_seen=datetime.now(),
                            last_seen=datetime.now(),
                            significance=confidence,
                        )
                    )

        return patterns

    def _detect_user_clusters(self) -> list[DetectedPattern]:
        """Détecte les groupes d'utilisateurs similaires"""
        patterns = []

        if len(self.user_profiles) < 3:
            return patterns

        # Créer vecteurs de caractéristiques utilisateur
        user_vectors = {}
        all_actions = set()

        for _user_id, profile in self.user_profiles.items():
            actions = profile.get("actions", {})
            all_actions.update(actions.keys())

        # Créer matrice utilisateur-action
        for user_id, profile in self.user_profiles.items():
            actions = profile.get("actions", {})
            vector = [actions.get(action, 0) for action in sorted(all_actions)]

            # Normaliser
            total = sum(vector)
            if total > 0:
                vector = [v / total for v in vector]
                user_vectors[user_id] = vector

        # Clustering simple basé sur similarité cosinus
        clusters = self._simple_clustering(user_vectors)

        for cluster_id, users in clusters.items():
            if len(users) >= 2:
                confidence = min(0.8, len(users) / len(user_vectors))
                patterns.append(
                    DetectedPattern(
                        pattern_id=f"user_cluster_{cluster_id}",
                        pattern_type=PatternType.CLUSTERING,
                        confidence=confidence,
                        description=f"Groupe d'utilisateurs similaires ({len(users)} utilisateurs)",
                        evidence={
                            "cluster_id": cluster_id,
                            "users": users,
                            "cluster_size": len(users),
                        },
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        significance=confidence,
                    )
                )

        return patterns

    def _simple_clustering(self, user_vectors: dict, threshold: float = 0.7) -> dict:
        """Clustering simple basé sur similarité"""
        clusters = defaultdict(list)
        cluster_id = 0

        for user1, vector1 in user_vectors.items():
            assigned = False

            for cid, cluster_users in clusters.items():
                if cluster_users:
                    # Calculer similarité avec premier utilisateur du cluster
                    first_user = cluster_users[0]
                    vector2 = user_vectors[first_user]
                    similarity = self._cosine_similarity(vector1, vector2)

                    if similarity > threshold:
                        clusters[cid].append(user1)
                        assigned = True
                        break

            if not assigned:
                clusters[cluster_id].append(user1)
                cluster_id += 1

        return dict(clusters)

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calcule similarité cosinus"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class PatternAnalyzer:
    """Analyseur principal de patterns"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.temporal_analyzer = TemporalAnalyzer(self.config.temporal_window_minutes)
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.detected_patterns: dict[str, DetectedPattern] = {}

    def analyze_patterns(self, events: list[dict]) -> list[DetectedPattern]:
        """Analyse tous les types de patterns"""
        all_patterns = []

        try:
            # Analyse temporelle
            if self.config.enable_temporal_analysis:
                temporal_patterns = self.temporal_analyzer.analyze_temporal_patterns(events)
                all_patterns.extend(temporal_patterns)

            # Analyse comportementale
            if self.config.enable_behavioral_analysis:
                behavioral_patterns = self.behavioral_analyzer.analyze_behavioral_patterns(events)
                all_patterns.extend(behavioral_patterns)

            # Filtrer par seuils de confiance et significance
            filtered_patterns = [
                p
                for p in all_patterns
                if p.confidence >= self.config.min_confidence_threshold
                and p.significance >= self.config.min_significance_threshold
            ]

            # Mettre à jour patterns détectés
            self._update_pattern_storage(filtered_patterns)

            logger.info(
                f"Analysé {len(events)} événements, détecté {len(filtered_patterns)} patterns"
            )
            return filtered_patterns

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de patterns: {e}")
            return []

    def _update_pattern_storage(self, patterns: list[DetectedPattern]):
        """Met à jour le stockage des patterns détectés"""
        for pattern in patterns:
            if pattern.pattern_id in self.detected_patterns:
                # Pattern existant - mettre à jour
                existing = self.detected_patterns[pattern.pattern_id]
                existing.last_seen = pattern.last_seen
                existing.occurrences += 1
                existing.confidence = (existing.confidence + pattern.confidence) / 2
            else:
                # Nouveau pattern
                if len(self.detected_patterns) < self.config.max_patterns_to_track:
                    self.detected_patterns[pattern.pattern_id] = pattern

    def get_top_patterns(self, limit: int = 10) -> list[DetectedPattern]:
        """Retourne les patterns les plus significatifs"""
        sorted_patterns = sorted(
            self.detected_patterns.values(),
            key=lambda p: p.significance * p.confidence,
            reverse=True,
        )
        return sorted_patterns[:limit]

    def get_patterns_by_type(self, pattern_type: PatternType) -> list[DetectedPattern]:
        """Retourne les patterns d'un type spécifique"""
        return [
            pattern
            for pattern in self.detected_patterns.values()
            if pattern.pattern_type == pattern_type
        ]

    def clear_old_patterns(self, hours: int = 24):
        """Supprime les patterns anciens"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        old_patterns = [
            pid
            for pid, pattern in self.detected_patterns.items()
            if pattern.last_seen < cutoff_time
        ]

        for pid in old_patterns:
            del self.detected_patterns[pid]

        logger.info(f"Supprimé {len(old_patterns)} patterns anciens")


# Instance globale
default_pattern_analyzer = PatternAnalyzer()
