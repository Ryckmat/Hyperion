"""
Hyperion v3.0 - Cache Analytics
Analyse et métriques pour le système de cache
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Métriques de cache"""

    hit_count: int = 0
    miss_count: int = 0
    set_count: int = 0
    delete_count: int = 0
    total_operations: int = 0
    start_time: float = 0.0


class CacheAnalytics:
    """Analyseur de performance cache"""

    def __init__(self):
        self.metrics = CacheMetrics(start_time=time.time())
        self.key_stats: dict[str, dict] = defaultdict(
            lambda: {"hits": 0, "misses": 0, "last_access": 0}
        )

    def record_hit(self, key: str):
        """Enregistre un cache hit"""
        self.metrics.hit_count += 1
        self.metrics.total_operations += 1
        self.key_stats[key]["hits"] += 1
        self.key_stats[key]["last_access"] = time.time()

    def record_miss(self, key: str):
        """Enregistre un cache miss"""
        self.metrics.miss_count += 1
        self.metrics.total_operations += 1
        self.key_stats[key]["misses"] += 1
        self.key_stats[key]["last_access"] = time.time()

    def record_set(self, _key: str):
        """Enregistre un cache set"""
        self.metrics.set_count += 1
        self.metrics.total_operations += 1

    def record_delete(self, _key: str):
        """Enregistre un cache delete"""
        self.metrics.delete_count += 1
        self.metrics.total_operations += 1

    def get_hit_rate(self) -> float:
        """Calcule le taux de hit"""
        total = self.metrics.hit_count + self.metrics.miss_count
        return self.metrics.hit_count / total if total > 0 else 0.0

    def get_statistics(self) -> dict[str, Any]:
        """Retourne les statistiques complètes"""
        uptime = time.time() - self.metrics.start_time
        hit_rate = self.get_hit_rate()

        return {
            "hit_count": self.metrics.hit_count,
            "miss_count": self.metrics.miss_count,
            "hit_rate": hit_rate,
            "hit_rate_percent": hit_rate * 100,
            "total_operations": self.metrics.total_operations,
            "uptime_seconds": uptime,
            "ops_per_second": self.metrics.total_operations / uptime if uptime > 0 else 0,
        }

    def get_top_keys(self, limit: int = 10) -> list[dict]:
        """Retourne les clés les plus utilisées"""
        sorted_keys = sorted(
            self.key_stats.items(), key=lambda x: x[1]["hits"] + x[1]["misses"], reverse=True
        )

        return [
            {
                "key": key,
                "total_accesses": stats["hits"] + stats["misses"],
                "hit_rate": (
                    stats["hits"] / (stats["hits"] + stats["misses"])
                    if (stats["hits"] + stats["misses"]) > 0
                    else 0
                ),
                "last_access": stats["last_access"],
            }
            for key, stats in sorted_keys[:limit]
        ]


# Instance globale
default_cache_analytics = CacheAnalytics()
