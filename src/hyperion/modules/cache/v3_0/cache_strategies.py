"""
Hyperion v3.0 - Cache Strategies
Stratégies de cache pour le système distribué
"""

import logging
import time
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class EvictionPolicy(Enum):
    """Politiques d'éviction du cache"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out


class CacheStrategy(ABC):
    """Interface de base pour les stratégies de cache"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.access_times = {}
        self.access_counts = {}

    @abstractmethod
    def should_evict(self, current_size: int) -> bool:
        """Détermine si une éviction est nécessaire"""
        pass

    @abstractmethod
    def select_eviction_keys(self, _cache_data: dict) -> list[str]:
        """Sélectionne les clés à évincer"""
        pass

    def record_access(self, key: str):
        """Enregistre l'accès à une clé"""
        current_time = time.time()
        self.access_times[key] = current_time
        self.access_counts[key] = self.access_counts.get(key, 0) + 1


class LRUStrategy(CacheStrategy):
    """Stratégie Least Recently Used"""

    def should_evict(self, current_size: int) -> bool:
        return current_size >= self.max_size

    def select_eviction_keys(self, _cache_data: dict) -> list[str]:
        if not self.access_times:
            return []

        # Trier par temps d'accès (plus ancien d'abord)
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])

        # Retourner la clé la moins récemment utilisée
        return [sorted_keys[0][0]] if sorted_keys else []


class LFUStrategy(CacheStrategy):
    """Stratégie Least Frequently Used"""

    def should_evict(self, current_size: int) -> bool:
        return current_size >= self.max_size

    def select_eviction_keys(self, _cache_data: dict) -> list[str]:
        if not self.access_counts:
            return []

        # Trier par nombre d'accès (moins fréquent d'abord)
        sorted_keys = sorted(self.access_counts.items(), key=lambda x: x[1])

        return [sorted_keys[0][0]] if sorted_keys else []


class TTLStrategy(CacheStrategy):
    """Stratégie Time To Live"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        super().__init__(max_size)
        self.default_ttl = default_ttl
        self.expiry_times = {}

    def should_evict(self, current_size: int) -> bool:
        # Éviction proactive des éléments expirés
        expired_keys = self._get_expired_keys()
        return len(expired_keys) > 0 or current_size >= self.max_size

    def select_eviction_keys(self, _cache_data: dict) -> list[str]:
        # D'abord les clés expirées
        expired_keys = self._get_expired_keys()
        if expired_keys:
            return expired_keys

        # Puis les plus proches de l'expiration
        if self.expiry_times:
            sorted_keys = sorted(self.expiry_times.items(), key=lambda x: x[1])
            return [sorted_keys[0][0]] if sorted_keys else []

        return []

    def set_ttl(self, key: str, ttl: int | None = None):
        """Définit le TTL pour une clé"""
        ttl = ttl or self.default_ttl
        self.expiry_times[key] = time.time() + ttl

    def _get_expired_keys(self) -> list[str]:
        """Retourne les clés expirées"""
        current_time = time.time()
        expired = [
            key for key, expiry_time in self.expiry_times.items() if expiry_time < current_time
        ]

        # Nettoyer les entrées expirées
        for key in expired:
            self.expiry_times.pop(key, None)
            self.access_times.pop(key, None)
            self.access_counts.pop(key, None)

        return expired


class AdaptiveStrategy(CacheStrategy):
    """Stratégie adaptative qui combine plusieurs approches"""

    def __init__(self, max_size: int = 1000):
        super().__init__(max_size)
        self.lru_strategy = LRUStrategy(max_size)
        self.lfu_strategy = LFUStrategy(max_size)
        self.ttl_strategy = TTLStrategy(max_size)

        # Poids pour les différentes stratégies
        self.lru_weight = 0.4
        self.lfu_weight = 0.3
        self.ttl_weight = 0.3

    def should_evict(self, current_size: int) -> bool:
        return any(
            [
                self.lru_strategy.should_evict(current_size),
                self.lfu_strategy.should_evict(current_size),
                self.ttl_strategy.should_evict(current_size),
            ]
        )

    def select_eviction_keys(self, cache_data: dict) -> list[str]:
        # Priorité aux clés expirées
        ttl_keys = self.ttl_strategy.select_eviction_keys(cache_data)
        if ttl_keys:
            return ttl_keys

        # Score combiné pour les autres stratégies
        all_keys = set(cache_data.keys())
        key_scores = {}

        for key in all_keys:
            lru_score = self._calculate_lru_score(key)
            lfu_score = self._calculate_lfu_score(key)

            combined_score = lru_score * self.lru_weight + lfu_score * self.lfu_weight

            key_scores[key] = combined_score

        if key_scores:
            # Retourner la clé avec le score le plus élevé (à évincer en priorité)
            worst_key = max(key_scores.items(), key=lambda x: x[1])
            return [worst_key[0]]

        return []

    def _calculate_lru_score(self, key: str) -> float:
        """Calcule le score LRU (plus élevé = plus ancien)"""
        if key not in self.access_times:
            return 1.0

        time_since_access = time.time() - self.access_times[key]
        return min(time_since_access / 3600, 1.0)  # Normaliser sur 1 heure

    def _calculate_lfu_score(self, key: str) -> float:
        """Calcule le score LFU (plus élevé = moins fréquent)"""
        if key not in self.access_counts:
            return 1.0

        access_count = self.access_counts[key]
        max_count = max(self.access_counts.values()) if self.access_counts else 1

        return 1.0 - (access_count / max_count)  # Inverser pour que moins = plus élevé

    def record_access(self, key: str):
        """Enregistre l'accès dans toutes les stratégies"""
        super().record_access(key)
        self.lru_strategy.record_access(key)
        self.lfu_strategy.record_access(key)


def create_cache_strategy(policy: EvictionPolicy, **kwargs) -> CacheStrategy:
    """Factory pour créer une stratégie de cache"""

    strategies = {
        EvictionPolicy.LRU: LRUStrategy,
        EvictionPolicy.LFU: LFUStrategy,
        EvictionPolicy.TTL: TTLStrategy,
    }

    if policy in strategies:
        return strategies[policy](**kwargs)
    else:
        logger.warning(f"Politique {policy} non supportée, utilisation de LRU")
        return LRUStrategy(**kwargs)


# Instance globale pour stratégie adaptative
default_adaptive_strategy = AdaptiveStrategy()
