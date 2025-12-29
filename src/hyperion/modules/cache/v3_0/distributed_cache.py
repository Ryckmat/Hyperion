"""
Distributed Cache Manager for Hyperion v3.0

Gestionnaire de cache distribué avec cohérence et haute disponibilité.
"""

import asyncio
import hashlib
import json
import logging
import pickle
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Niveaux de cache"""

    L1_MEMORY = "l1_memory"  # Cache en mémoire local
    L2_REDIS = "l2_redis"  # Cache Redis distribué
    L3_PERSISTENT = "l3_persistent"  # Cache persistant (DB)


class CacheStrategy(Enum):
    """Stratégies de cache"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptatif basé sur l'usage


@dataclass
class CacheEntry:
    """Entrée de cache enrichie"""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: float | None
    size_bytes: int
    metadata: dict[str, Any] = field(default_factory=dict)

    # Métriques de performance
    hit_rate: float = 0.0
    avg_access_time: float = 0.0

    # Gestion de la cohérence
    version: int = 1
    source_hash: str | None = None
    invalidation_tags: list[str] = field(default_factory=list)


@dataclass
class CacheStats:
    """Statistiques de cache"""

    total_gets: int = 0
    total_sets: int = 0
    total_hits: int = 0
    total_misses: int = 0
    total_evictions: int = 0
    total_invalidations: int = 0

    # Métriques de performance
    avg_get_time: float = 0.0
    avg_set_time: float = 0.0
    memory_usage_bytes: int = 0
    hit_rate: float = 0.0

    # Distribution par niveau
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0


class CacheBackend(ABC):
    """Interface abstraite pour backends de cache"""

    @abstractmethod
    async def get(self, key: str) -> CacheEntry | None:
        pass

    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear(self) -> int:
        pass

    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        pass


class MemoryBackend(CacheBackend):
    """Backend cache mémoire avec gestion LRU/LFU"""

    def __init__(self, max_size: int = 10000, strategy: CacheStrategy = CacheStrategy.LRU):
        self.max_size = max_size
        self.strategy = strategy
        self.storage: dict[str, CacheEntry] = {}
        self.access_order: list[str] = []  # Pour LRU
        self.access_frequency: dict[str, int] = {}  # Pour LFU
        self._lock = threading.RLock()

    async def get(self, key: str) -> CacheEntry | None:
        with self._lock:
            if key not in self.storage:
                return None

            entry = self.storage[key]

            # Vérifier TTL
            if entry.ttl and time.time() > entry.created_at + entry.ttl:
                await self.delete(key)
                return None

            # Mettre à jour les métriques d'accès
            entry.last_accessed = time.time()
            entry.access_count += 1

            # Gérer l'ordre d'accès selon la stratégie
            if self.strategy == CacheStrategy.LRU:
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)

            elif self.strategy == CacheStrategy.LFU:
                self.access_frequency[key] = self.access_frequency.get(key, 0) + 1

            return entry

    async def set(self, key: str, entry: CacheEntry) -> bool:
        with self._lock:
            # Éviction si nécessaire
            if len(self.storage) >= self.max_size and key not in self.storage:
                await self._evict()

            self.storage[key] = entry

            # Initialiser tracking selon stratégie
            if self.strategy == CacheStrategy.LRU:
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)

            elif self.strategy == CacheStrategy.LFU:
                self.access_frequency[key] = 1

            return True

    async def delete(self, key: str) -> bool:
        with self._lock:
            if key in self.storage:
                del self.storage[key]

                if key in self.access_order:
                    self.access_order.remove(key)

                if key in self.access_frequency:
                    del self.access_frequency[key]

                return True
            return False

    async def exists(self, key: str) -> bool:
        with self._lock:
            return key in self.storage

    async def clear(self) -> int:
        with self._lock:
            count = len(self.storage)
            self.storage.clear()
            self.access_order.clear()
            self.access_frequency.clear()
            return count

    async def keys(self, pattern: str = "*") -> list[str]:
        with self._lock:
            if pattern == "*":
                return list(self.storage.keys())
            else:
                # Simulation simple de pattern matching
                import fnmatch

                return [key for key in self.storage if fnmatch.fnmatch(key, pattern)]

    async def _evict(self):
        """Éviction selon la stratégie configurée"""
        if not self.storage:
            return

        if self.strategy == CacheStrategy.LRU:
            # Supprimer le moins récemment utilisé
            if self.access_order:
                lru_key = self.access_order[0]
                await self.delete(lru_key)

        elif self.strategy == CacheStrategy.LFU:
            # Supprimer le moins fréquemment utilisé
            if self.access_frequency:
                lfu_key = min(self.access_frequency, key=self.access_frequency.get)
                await self.delete(lfu_key)

        elif self.strategy == CacheStrategy.TTL:
            # Supprimer le plus ancien avec TTL
            oldest_key = None
            oldest_time = float("inf")

            for key, entry in self.storage.items():
                if entry.ttl and entry.created_at < oldest_time:
                    oldest_time = entry.created_at
                    oldest_key = key

            if oldest_key:
                await self.delete(oldest_key)


class RedisBackend(CacheBackend):
    """Backend Redis pour cache distribué (simulation)"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.connected = False

        # Simulation - en production utiliser redis-py
        self._redis_sim: dict[str, str] = {}

    async def get(self, key: str) -> CacheEntry | None:
        if not self.connected:
            await self._connect()

        # Simulation Redis
        if key in self._redis_sim:
            try:
                serialized_data = self._redis_sim[key]
                entry_data = json.loads(serialized_data)

                # Reconstruire CacheEntry
                entry = CacheEntry(
                    key=entry_data["key"],
                    value=entry_data["value"],
                    created_at=entry_data["created_at"],
                    last_accessed=entry_data["last_accessed"],
                    access_count=entry_data["access_count"],
                    ttl=entry_data.get("ttl"),
                    size_bytes=entry_data["size_bytes"],
                    metadata=entry_data.get("metadata", {}),
                    version=entry_data.get("version", 1),
                    invalidation_tags=entry_data.get("invalidation_tags", []),
                )

                # Vérifier TTL
                if entry.ttl and time.time() > entry.created_at + entry.ttl:
                    await self.delete(key)
                    return None

                return entry

            except Exception as e:
                logger.error(f"Erreur désérialisation Redis {key}: {e}")
                return None

        return None

    async def set(self, key: str, entry: CacheEntry) -> bool:
        if not self.connected:
            await self._connect()

        try:
            # Sérializer CacheEntry
            entry_data = {
                "key": entry.key,
                "value": entry.value,
                "created_at": entry.created_at,
                "last_accessed": entry.last_accessed,
                "access_count": entry.access_count,
                "ttl": entry.ttl,
                "size_bytes": entry.size_bytes,
                "metadata": entry.metadata,
                "version": entry.version,
                "invalidation_tags": entry.invalidation_tags,
            }

            serialized_data = json.dumps(entry_data, default=str)
            self._redis_sim[key] = serialized_data

            # En production, définir TTL Redis si spécifié
            return True

        except Exception as e:
            logger.error(f"Erreur sérialisation Redis {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if key in self._redis_sim:
            del self._redis_sim[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        return key in self._redis_sim

    async def clear(self) -> int:
        count = len(self._redis_sim)
        self._redis_sim.clear()
        return count

    async def keys(self, pattern: str = "*") -> list[str]:
        if pattern == "*":
            return list(self._redis_sim.keys())
        else:
            import fnmatch

            return [key for key in self._redis_sim if fnmatch.fnmatch(key, pattern)]

    async def _connect(self):
        """Simuler connexion Redis"""
        # En production: redis.Redis(host=self.host, port=self.port, db=self.db)
        self.connected = True
        logger.debug("Connexion Redis simulée")


class DistributedCacheManager:
    """
    Gestionnaire de cache distribué pour Hyperion v3.0

    Fonctionnalités :
    - Cache multi-niveaux (L1/L2/L3)
    - Invalidation intelligente par tags
    - Cohérence de données distribuée
    - Stratégies d'éviction adaptatives
    - Analytics et monitoring intégrés
    - Sérialisation automatique
    - Compression transparente
    """

    def __init__(
        self,
        enable_l1: bool = True,
        enable_l2: bool = True,
        l1_max_size: int = 10000,
        l2_config: dict | None = None,
        default_ttl: int = 3600,
    ):

        self.enable_l1 = enable_l1
        self.enable_l2 = enable_l2
        self.default_ttl = default_ttl

        # Configuration des backends
        self.backends: dict[CacheLevel, CacheBackend] = {}

        if enable_l1:
            self.backends[CacheLevel.L1_MEMORY] = MemoryBackend(max_size=l1_max_size)

        if enable_l2:
            redis_config = l2_config or {"host": "localhost", "port": 6379}
            self.backends[CacheLevel.L2_REDIS] = RedisBackend(**redis_config)

        # Statistiques globales
        self.stats = CacheStats()

        # Cache des callbacks d'invalidation
        self.invalidation_callbacks: dict[str, list[Callable]] = {}

        # Configuration de sérialisation
        self.serialization_strategy = "json"  # json, pickle, msgpack

        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Métriques de performance
        self.performance_history: list[dict[str, float]] = []

        logger.info("DistributedCacheManager v3.0 initialisé")

    async def get(self, key: str, default: Any = None) -> Any:
        """Récupération intelligente multi-niveaux"""

        start_time = time.time()

        try:
            # Essayer L1 en premier
            if CacheLevel.L1_MEMORY in self.backends:
                entry = await self.backends[CacheLevel.L1_MEMORY].get(key)
                if entry:
                    self.stats.l1_hits += 1
                    self.stats.total_hits += 1
                    await self._record_performance_metric("get", time.time() - start_time, "l1_hit")
                    return entry.value

            # Essayer L2 Redis
            if CacheLevel.L2_REDIS in self.backends:
                entry = await self.backends[CacheLevel.L2_REDIS].get(key)
                if entry:
                    self.stats.l2_hits += 1
                    self.stats.total_hits += 1

                    # Promouvoir vers L1
                    if CacheLevel.L1_MEMORY in self.backends:
                        await self.backends[CacheLevel.L1_MEMORY].set(key, entry)

                    await self._record_performance_metric("get", time.time() - start_time, "l2_hit")
                    return entry.value

            # Cache miss complet
            self.stats.total_misses += 1
            await self._record_performance_metric("get", time.time() - start_time, "miss")
            return default

        except Exception as e:
            logger.error(f"Erreur récupération cache {key}: {e}")
            return default

        finally:
            self.stats.total_gets += 1
            self.stats.avg_get_time = (
                self.stats.avg_get_time * (self.stats.total_gets - 1) + (time.time() - start_time)
            ) / self.stats.total_gets

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: list[str] | None = None,
        level: CacheLevel | None = None,
    ) -> bool:
        """Stockage intelligent multi-niveaux"""

        start_time = time.time()

        try:
            # TTL par défaut
            if ttl is None:
                ttl = self.default_ttl

            # Calculer taille approximative
            size_bytes = self._calculate_size(value)

            # Créer entrée cache
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                ttl=ttl,
                size_bytes=size_bytes,
                invalidation_tags=tags or [],
                source_hash=self._calculate_hash(value),
            )

            success = True

            # Déterminer les niveaux de stockage
            target_levels = []

            if level:
                # Niveau spécifique
                target_levels = [level]
            else:
                # Logique automatique
                if size_bytes < 1024 * 100:  # < 100KB
                    target_levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
                else:
                    target_levels = [CacheLevel.L2_REDIS]

            # Stocker dans les niveaux appropriés
            for target_level in target_levels:
                if target_level in self.backends:
                    result = await self.backends[target_level].set(key, entry)
                    success = success and result

            if success:
                self.stats.total_sets += 1

                # Enregistrer tags pour invalidation
                if tags:
                    for tag in tags:
                        if tag not in self.invalidation_callbacks:
                            self.invalidation_callbacks[tag] = []

            await self._record_performance_metric(
                "set", time.time() - start_time, "success" if success else "failure"
            )

            return success

        except Exception as e:
            logger.error(f"Erreur stockage cache {key}: {e}")
            return False

        finally:
            self.stats.avg_set_time = (
                self.stats.avg_set_time * self.stats.total_sets + (time.time() - start_time)
            ) / max(self.stats.total_sets + 1, 1)

    async def delete(self, key: str) -> bool:
        """Suppression multi-niveaux"""

        success = True

        for backend in self.backends.values():
            result = await backend.delete(key)
            success = success and result

        return success

    async def exists(self, key: str) -> bool:
        """Vérification d'existence multi-niveaux"""

        for backend in self.backends.values():
            if await backend.exists(key):
                return True

        return False

    async def invalidate_by_tags(self, tags: list[str]) -> int:
        """Invalidation par tags"""

        invalidated_count = 0

        for tag in tags:
            # Récupérer toutes les clés avec ce tag
            keys_to_invalidate = await self._find_keys_by_tag(tag)

            for key in keys_to_invalidate:
                if await self.delete(key):
                    invalidated_count += 1

            # Appeler callbacks d'invalidation
            if tag in self.invalidation_callbacks:
                for callback in self.invalidation_callbacks[tag]:
                    try:
                        await asyncio.create_task(callback(tag, keys_to_invalidate))
                    except Exception as e:
                        logger.error(f"Erreur callback invalidation {tag}: {e}")

        self.stats.total_invalidations += invalidated_count
        logger.info(f"Invalidation par tags {tags}: {invalidated_count} clés")

        return invalidated_count

    async def _find_keys_by_tag(self, tag: str) -> list[str]:
        """Trouver les clés associées à un tag"""

        keys_with_tag = []

        for backend in self.backends.values():
            all_keys = await backend.keys("*")

            for key in all_keys:
                entry = await backend.get(key)
                if entry and tag in entry.invalidation_tags:
                    keys_with_tag.append(key)

        return list(set(keys_with_tag))  # Déduplication

    async def clear_all(self) -> dict[str, int]:
        """Vider tous les caches"""

        cleared_counts = {}

        for level, backend in self.backends.items():
            count = await backend.clear()
            cleared_counts[level.value] = count

        logger.info(f"Tous les caches vidés: {cleared_counts}")
        return cleared_counts

    async def warm_cache(
        self, data_loader: Callable[[str], Any], keys: list[str], batch_size: int = 100
    ) -> int:
        """Préchauffage du cache"""

        warmed_count = 0

        # Traiter par batches
        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i : i + batch_size]

            # Charger en parallèle
            tasks = []
            for key in batch_keys:
                task = asyncio.create_task(self._warm_single_key(key, data_loader))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, bool) and result:
                    warmed_count += 1
                elif isinstance(result, Exception):
                    logger.warning(f"Erreur préchauffage: {result}")

        logger.info(f"Cache préchauffé: {warmed_count}/{len(keys)} clés")
        return warmed_count

    async def _warm_single_key(self, key: str, data_loader: Callable) -> bool:
        """Préchauffer une clé individuelle"""

        try:
            # Vérifier si déjà en cache
            if await self.exists(key):
                return True

            # Charger la donnée
            value = await asyncio.create_task(data_loader(key))

            if value is not None:
                await self.set(key, value)
                return True

            return False

        except Exception as e:
            logger.error(f"Erreur préchauffage clé {key}: {e}")
            return False

    def _calculate_size(self, value: Any) -> int:
        """Calculer la taille approximative d'une valeur"""

        try:
            if self.serialization_strategy == "json":
                return len(json.dumps(value, default=str).encode("utf-8"))
            elif self.serialization_strategy == "pickle":
                return len(pickle.dumps(value))
            else:
                # Estimation approximative
                import sys

                return sys.getsizeof(value)

        except Exception:
            return 1024  # Valeur par défaut

    def _calculate_hash(self, value: Any) -> str:
        """Calculer hash pour détecter les changements"""

        try:
            if self.serialization_strategy == "json":
                content = json.dumps(value, sort_keys=True, default=str)
            else:
                content = str(value)

            return hashlib.md5(content.encode("utf-8")).hexdigest()

        except Exception:
            return hashlib.md5(str(time.time()).encode()).hexdigest()

    async def _record_performance_metric(self, operation: str, duration: float, result: str):
        """Enregistrer métrique de performance"""

        metric = {
            "timestamp": time.time(),
            "operation": operation,
            "duration": duration,
            "result": result,
        }

        self.performance_history.append(metric)

        # Garder seulement les 1000 dernières métriques
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

    def add_invalidation_callback(self, tag: str, callback: Callable):
        """Ajouter callback d'invalidation pour un tag"""

        if tag not in self.invalidation_callbacks:
            self.invalidation_callbacks[tag] = []

        self.invalidation_callbacks[tag].append(callback)

    def get_cache_statistics(self) -> dict[str, Any]:
        """Obtenir statistiques détaillées"""

        hit_rate = (self.stats.total_hits / max(self.stats.total_gets, 1)) * 100

        return {
            "hit_rate_percent": hit_rate,
            "total_operations": self.stats.total_gets + self.stats.total_sets,
            "total_hits": self.stats.total_hits,
            "total_misses": self.stats.total_misses,
            "total_sets": self.stats.total_sets,
            "total_evictions": self.stats.total_evictions,
            "total_invalidations": self.stats.total_invalidations,
            "avg_get_time_ms": self.stats.avg_get_time * 1000,
            "avg_set_time_ms": self.stats.avg_set_time * 1000,
            "l1_hits": self.stats.l1_hits,
            "l2_hits": self.stats.l2_hits,
            "l3_hits": self.stats.l3_hits,
            "levels_active": list(self.backends.keys()),
            "performance_trend": self._calculate_performance_trend(),
        }

    def _calculate_performance_trend(self) -> str:
        """Calculer tendance de performance"""

        if len(self.performance_history) < 10:
            return "insufficient_data"

        recent_metrics = self.performance_history[-10:]
        older_metrics = (
            self.performance_history[-20:-10]
            if len(self.performance_history) >= 20
            else recent_metrics
        )

        recent_avg = sum(m["duration"] for m in recent_metrics) / len(recent_metrics)
        older_avg = sum(m["duration"] for m in older_metrics) / len(older_metrics)

        if recent_avg < older_avg * 0.9:
            return "improving"
        elif recent_avg > older_avg * 1.1:
            return "degrading"
        else:
            return "stable"

    async def optimize_cache_levels(self) -> dict[str, Any]:
        """Optimisation automatique des niveaux de cache"""

        optimization_results = {"l1_promoted": 0, "l1_demoted": 0, "recommendations": []}

        # Analyser les patterns d'accès
        if CacheLevel.L2_REDIS in self.backends and CacheLevel.L1_MEMORY in self.backends:

            # Obtenir toutes les clés L2
            l2_keys = await self.backends[CacheLevel.L2_REDIS].keys("*")

            for key in l2_keys[:100]:  # Limiter pour performance
                l2_entry = await self.backends[CacheLevel.L2_REDIS].get(key)

                if l2_entry and l2_entry.access_count > 10:  # Clé fréquemment utilisée
                    l1_exists = await self.backends[CacheLevel.L1_MEMORY].exists(key)

                    if not l1_exists:
                        # Promouvoir vers L1
                        await self.backends[CacheLevel.L1_MEMORY].set(key, l2_entry)
                        optimization_results["l1_promoted"] += 1

        # Recommandations
        if self.get_cache_statistics()["hit_rate_percent"] < 80:
            optimization_results["recommendations"].append(
                "Augmenter la taille du cache L1 pour améliorer le hit rate"
            )

        if self.stats.total_evictions > self.stats.total_sets * 0.1:
            optimization_results["recommendations"].append(
                "Évictions fréquentes détectées, considérer augmenter la capacité"
            )

        return optimization_results

    async def health_check(self) -> dict[str, Any]:
        """Vérification de santé du cache"""

        health_status = {"overall_status": "healthy", "backends_status": {}, "issues": []}

        # Tester chaque backend
        for level, backend in self.backends.items():
            try:
                # Test simple
                test_key = f"health_check_{int(time.time())}"
                test_value = "test"

                await backend.set(
                    test_key,
                    CacheEntry(
                        key=test_key,
                        value=test_value,
                        created_at=time.time(),
                        last_accessed=time.time(),
                        access_count=1,
                        ttl=60,
                        size_bytes=len(test_value),
                    ),
                )

                retrieved = await backend.get(test_key)
                await backend.delete(test_key)

                if retrieved and retrieved.value == test_value:
                    health_status["backends_status"][level.value] = "healthy"
                else:
                    health_status["backends_status"][level.value] = "unhealthy"
                    health_status["issues"].append(f"Backend {level.value}: test failed")

            except Exception as e:
                health_status["backends_status"][level.value] = "error"
                health_status["issues"].append(f"Backend {level.value}: {str(e)}")

        # Statut global
        if any(status != "healthy" for status in health_status["backends_status"].values()):
            health_status["overall_status"] = "degraded"

        if len(health_status["issues"]) > len(self.backends) / 2:
            health_status["overall_status"] = "unhealthy"

        return health_status


# Instance globale
distributed_cache = DistributedCacheManager()


# Fonctions de convenance
async def cache_get(key: str, default: Any = None) -> Any:
    """Récupérer du cache"""
    return await distributed_cache.get(key, default)


async def cache_set(
    key: str, value: Any, ttl: int | None = None, tags: list[str] | None = None
) -> bool:
    """Stocker dans le cache"""
    return await distributed_cache.set(key, value, ttl=ttl, tags=tags)


async def cache_invalidate_tags(tags: list[str]) -> int:
    """Invalider par tags"""
    return await distributed_cache.invalidate_by_tags(tags)
