"""
Hyperion v3.0 - Cache Invalidation Engine
Moteur d'invalidation intelligent pour le cache distribué
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class InvalidationType(Enum):
    """Types d'invalidation"""

    TTL = "ttl"  # Time to Live
    TAG = "tag"  # Par tag
    PATTERN = "pattern"  # Par pattern
    MANUAL = "manual"  # Manuel
    DEPENDENCY = "dependency"  # Par dépendance


@dataclass
class InvalidationRule:
    """Règle d'invalidation"""

    rule_id: str
    invalidation_type: InvalidationType
    pattern: str
    tags: set[str]
    ttl_seconds: int | None = None


class InvalidationEngine:
    """Moteur d'invalidation de cache"""

    def __init__(self):
        self.rules: dict[str, InvalidationRule] = {}
        self.key_dependencies: dict[str, set[str]] = {}
        self.tag_mappings: dict[str, set[str]] = {}

    def add_rule(self, rule: InvalidationRule):
        """Ajoute une règle d'invalidation"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Règle d'invalidation ajoutée: {rule.rule_id}")

    def invalidate_by_pattern(self, pattern: str) -> list[str]:
        """Invalide les clés selon un pattern"""
        # Simulation d'invalidation par pattern
        invalidated_keys = [f"key_{i}" for i in range(5) if pattern in f"key_{i}"]
        logger.info(f"Invalidation par pattern '{pattern}': {len(invalidated_keys)} clés")
        return invalidated_keys

    def invalidate_by_tags(self, tags: set[str]) -> list[str]:
        """Invalide les clés par tags"""
        invalidated_keys = []
        for tag in tags:
            if tag in self.tag_mappings:
                invalidated_keys.extend(self.tag_mappings[tag])

        logger.info(f"Invalidation par tags {tags}: {len(invalidated_keys)} clés")
        return list(set(invalidated_keys))  # Dédoublonner

    def add_dependency(self, key: str, depends_on: str):
        """Ajoute une dépendance entre clés"""
        if key not in self.key_dependencies:
            self.key_dependencies[key] = set()
        self.key_dependencies[key].add(depends_on)

    def invalidate_dependencies(self, key: str) -> list[str]:
        """Invalide les clés dépendantes"""
        invalidated = []
        for dependent_key, dependencies in self.key_dependencies.items():
            if key in dependencies:
                invalidated.append(dependent_key)

        logger.info(f"Invalidation dépendances de '{key}': {len(invalidated)} clés")
        return invalidated


# Instance globale
default_invalidation_engine = InvalidationEngine()
