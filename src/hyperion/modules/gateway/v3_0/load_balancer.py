"""
Hyperion v3.0 - Load Balancer
Équilibreur de charge pour l'API Gateway
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LoadBalancingAlgorithm(Enum):
    """Algorithmes d'équilibrage de charge"""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    IP_HASH = "ip_hash"


@dataclass
class Backend:
    """Backend server"""

    id: str
    host: str
    port: int
    weight: float = 1.0
    healthy: bool = True
    current_connections: int = 0
    last_health_check: float = 0.0


class LoadBalancer:
    """Équilibreur de charge simple"""

    def __init__(self, algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN):
        self.algorithm = algorithm
        self.backends: list[Backend] = []
        self.current_index = 0

    def add_backend(self, backend: Backend):
        """Ajoute un backend"""
        self.backends.append(backend)
        logger.info(f"Backend ajouté: {backend.id}")

    def select_backend(self, _client_ip: str | None = None) -> Backend | None:
        """Sélectionne un backend selon l'algorithme"""
        healthy_backends = [b for b in self.backends if b.healthy]

        if not healthy_backends:
            return None

        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            backend = healthy_backends[self.current_index % len(healthy_backends)]
            self.current_index = (self.current_index + 1) % len(healthy_backends)
            return backend

        elif self.algorithm == LoadBalancingAlgorithm.RANDOM:
            return random.choice(healthy_backends)

        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return min(healthy_backends, key=lambda b: b.current_connections)

        return healthy_backends[0]  # Fallback
