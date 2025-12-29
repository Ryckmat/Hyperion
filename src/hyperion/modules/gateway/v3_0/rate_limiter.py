"""
Hyperion v3.0 - Rate Limiter
Système de limitation de taux pour l'API Gateway
"""

import logging
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """Algorithmes de limitation de taux"""

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimit:
    """Configuration de limitation de taux"""

    requests_per_second: int
    burst_capacity: int
    window_size: int = 60  # secondes
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET


@dataclass
class RateLimitResult:
    """Résultat d'une vérification de rate limiting"""

    allowed: bool
    remaining: int
    reset_time: float
    retry_after: int | None = None


class TokenBucket:
    """Implémentation Token Bucket"""

    def __init__(self, rate: int, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity  # max tokens
        self.tokens = float(capacity)
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Tente de consommer des tokens"""
        now = time.time()

        # Ajouter des tokens basés sur le temps écoulé
        time_passed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + time_passed * self.rate)
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_remaining(self) -> int:
        """Retourne le nombre de tokens restants"""
        now = time.time()
        time_passed = now - self.last_update
        current_tokens = min(self.capacity, self.tokens + time_passed * self.rate)
        return int(current_tokens)

    def get_reset_time(self) -> float:
        """Retourne quand le bucket sera plein"""
        if self.tokens >= self.capacity:
            return time.time()

        tokens_needed = self.capacity - self.tokens
        time_to_fill = tokens_needed / self.rate
        return time.time() + time_to_fill


class SlidingWindow:
    """Implémentation Sliding Window"""

    def __init__(self, rate: int, window_size: int = 60):
        self.rate = rate
        self.window_size = window_size
        self.requests = deque()

    def is_allowed(self) -> bool:
        """Vérifie si une requête est autorisée"""
        now = time.time()

        # Nettoyer les anciennes requêtes
        cutoff = now - self.window_size
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        if len(self.requests) < self.rate:
            self.requests.append(now)
            return True
        return False

    def get_remaining(self) -> int:
        """Retourne le nombre de requêtes restantes"""
        now = time.time()
        cutoff = now - self.window_size

        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        return max(0, self.rate - len(self.requests))

    def get_reset_time(self) -> float:
        """Retourne quand la fenêtre se réinitialisera"""
        if not self.requests:
            return time.time()
        return self.requests[0] + self.window_size


class FixedWindow:
    """Implémentation Fixed Window"""

    def __init__(self, rate: int, window_size: int = 60):
        self.rate = rate
        self.window_size = window_size
        self.request_count = 0
        self.window_start = time.time()

    def is_allowed(self) -> bool:
        """Vérifie si une requête est autorisée"""
        now = time.time()

        # Réinitialiser si nouvelle fenêtre
        if now - self.window_start >= self.window_size:
            self.request_count = 0
            self.window_start = now

        if self.request_count < self.rate:
            self.request_count += 1
            return True
        return False

    def get_remaining(self) -> int:
        """Retourne le nombre de requêtes restantes"""
        now = time.time()

        if now - self.window_start >= self.window_size:
            return self.rate
        return max(0, self.rate - self.request_count)

    def get_reset_time(self) -> float:
        """Retourne quand la fenêtre se réinitialisera"""
        return self.window_start + self.window_size


class RateLimiter:
    """Gestionnaire de limitation de taux"""

    def __init__(self):
        self.limiters: dict[str, Any] = {}
        self.rate_limits: dict[str, RateLimit] = {}

    def add_rate_limit(self, identifier: str, rate_limit: RateLimit):
        """Ajoute une configuration de rate limit"""
        self.rate_limits[identifier] = rate_limit

        if rate_limit.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            self.limiters[identifier] = TokenBucket(
                rate_limit.requests_per_second, rate_limit.burst_capacity
            )
        elif rate_limit.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            self.limiters[identifier] = SlidingWindow(
                rate_limit.requests_per_second * rate_limit.window_size, rate_limit.window_size
            )
        elif rate_limit.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            self.limiters[identifier] = FixedWindow(
                rate_limit.requests_per_second * rate_limit.window_size, rate_limit.window_size
            )

    async def check_rate_limit(self, identifier: str, client_key: str) -> RateLimitResult:
        """Vérifie la limitation de taux pour un client"""
        full_key = f"{identifier}:{client_key}"

        if identifier not in self.rate_limits:
            # Pas de limite configurée
            return RateLimitResult(allowed=True, remaining=999999, reset_time=time.time() + 3600)

        # Créer limiter pour ce client si inexistant
        if full_key not in self.limiters:
            rate_limit = self.rate_limits[identifier]
            if rate_limit.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                self.limiters[full_key] = TokenBucket(
                    rate_limit.requests_per_second, rate_limit.burst_capacity
                )
            elif rate_limit.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                self.limiters[full_key] = SlidingWindow(
                    rate_limit.requests_per_second * rate_limit.window_size, rate_limit.window_size
                )
            elif rate_limit.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                self.limiters[full_key] = FixedWindow(
                    rate_limit.requests_per_second * rate_limit.window_size, rate_limit.window_size
                )

        limiter = self.limiters[full_key]

        # Vérification spécifique selon l'algorithme
        if isinstance(limiter, TokenBucket):
            allowed = limiter.consume(1)
            remaining = limiter.get_remaining()
            reset_time = limiter.get_reset_time()
        else:  # SlidingWindow ou FixedWindow
            allowed = limiter.is_allowed()
            remaining = limiter.get_remaining()
            reset_time = limiter.get_reset_time()

        retry_after = None
        if not allowed:
            retry_after = int(reset_time - time.time())

        return RateLimitResult(
            allowed=allowed, remaining=remaining, reset_time=reset_time, retry_after=retry_after
        )

    def get_rate_limit_headers(self, result: RateLimitResult) -> dict[str, str]:
        """Génère les headers HTTP pour rate limiting"""
        headers = {
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_time)),
        }

        if result.retry_after is not None:
            headers["Retry-After"] = str(result.retry_after)

        return headers

    def cleanup_expired_limiters(self):
        """Nettoie les limiters expirés"""
        current_time = time.time()
        expired_keys = []

        for key, limiter in self.limiters.items():
            if isinstance(limiter, TokenBucket):
                # Supprimer si inactif depuis longtemps
                if current_time - limiter.last_update > 3600:  # 1 heure
                    expired_keys.append(key)
            elif hasattr(limiter, "window_start") and current_time - limiter.window_start > 3600:
                # Supprimer si fenêtre expirée depuis longtemps
                expired_keys.append(key)

        for key in expired_keys:
            del self.limiters[key]

        logger.info(f"Nettoyé {len(expired_keys)} limiters expirés")


# Configuration de rate limits prédéfinis
DEFAULT_RATE_LIMITS = {
    "api": RateLimit(
        requests_per_second=100, burst_capacity=200, algorithm=RateLimitAlgorithm.TOKEN_BUCKET
    ),
    "auth": RateLimit(
        requests_per_second=10, burst_capacity=20, algorithm=RateLimitAlgorithm.SLIDING_WINDOW
    ),
    "rag": RateLimit(
        requests_per_second=20, burst_capacity=40, algorithm=RateLimitAlgorithm.TOKEN_BUCKET
    ),
    "upload": RateLimit(
        requests_per_second=5, burst_capacity=10, algorithm=RateLimitAlgorithm.FIXED_WINDOW
    ),
}

# Instance globale
global_rate_limiter = RateLimiter()

# Configurer les limits par défaut
for identifier, rate_limit in DEFAULT_RATE_LIMITS.items():
    global_rate_limiter.add_rate_limit(identifier, rate_limit)
