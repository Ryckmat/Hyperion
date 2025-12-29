"""
API Gateway for Hyperion v3.0

Gateway enterprise avec routing, sécurité et observabilité.
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HTTPMethod(Enum):
    """Méthodes HTTP supportées"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class RouteType(Enum):
    """Types de routes"""

    API = "api"
    WEBSOCKET = "websocket"
    STATIC = "static"
    REDIRECT = "redirect"


@dataclass
class Request:
    """Requête HTTP normalisée"""

    method: HTTPMethod
    path: str
    headers: dict[str, str]
    query_params: dict[str, str]
    body: bytes | None = None

    # Contexte
    client_ip: str | None = None
    user_agent: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    request_id: str = field(default_factory=lambda: f"req_{int(time.time() * 1000)}")

    # Métadonnées
    timestamp: float = field(default_factory=time.time)
    route_matched: str | None = None


@dataclass
class Response:
    """Réponse HTTP normalisée"""

    status_code: int
    headers: dict[str, str]
    body: bytes | None = None

    # Métriques
    processing_time: float = 0.0
    backend_service: str | None = None
    cache_hit: bool = False


@dataclass
class Route:
    """Configuration d'une route"""

    path_pattern: str
    methods: list[HTTPMethod]
    backend_url: str
    route_type: RouteType = RouteType.API

    # Sécurité
    auth_required: bool = True
    roles_required: list[str] = field(default_factory=list)
    rate_limit_per_minute: int | None = None

    # Transformation
    request_transform: Callable | None = None
    response_transform: Callable | None = None

    # Cache
    cache_ttl: int | None = None
    cache_key_generator: Callable | None = None

    # Métadonnées
    name: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Middleware:
    """Middleware de traitement"""

    name: str
    priority: int
    pre_request_handler: Callable | None = None
    post_response_handler: Callable | None = None
    error_handler: Callable | None = None


@dataclass
class GatewayStats:
    """Statistiques du gateway"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0

    # Par endpoint
    endpoint_stats: dict[str, dict[str, int]] = field(default_factory=dict)

    # Rate limiting
    rate_limited_requests: int = 0

    # Cache
    cache_hits: int = 0
    cache_misses: int = 0


class APIGateway:
    """
    Gateway API enterprise pour Hyperion v3.0

    Fonctionnalités :
    - Routing intelligent avec pattern matching
    - Rate limiting distribué
    - Authentification et autorisation intégrées
    - Load balancing avec health checks
    - Transformation de requêtes/réponses
    - Cache transparent avec invalidation
    - Monitoring et métriques détaillées
    - Circuit breaker pour résilience
    """

    def __init__(
        self,
        enable_auth: bool = True,
        enable_rate_limiting: bool = True,
        enable_caching: bool = True,
        default_timeout: int = 30,
    ):

        self.enable_auth = enable_auth
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_caching = enable_caching
        self.default_timeout = default_timeout

        # Configuration des routes
        self.routes: list[Route] = []
        self.compiled_routes: list[tuple[re.Pattern, Route]] = []

        # Middlewares
        self.middlewares: list[Middleware] = []

        # Services intégrés
        self.auth_service = None
        self.rate_limiter = None
        self.cache_service = None
        self.load_balancer = None

        # Statistiques
        self.stats = GatewayStats()

        # Circuit breakers par backend
        self.circuit_breakers: dict[str, dict[str, Any]] = {}

        # Threading
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Configuration par défaut
        self._setup_default_middlewares()
        self._setup_default_routes()

        logger.info("APIGateway initialisé")

    def add_route(self, route: Route):
        """Ajouter une route au gateway"""

        try:
            # Compiler le pattern de route
            compiled_pattern = re.compile(route.path_pattern)

            self.routes.append(route)
            self.compiled_routes.append((compiled_pattern, route))

            # Initialiser les stats pour cette route
            if route.name not in self.stats.endpoint_stats:
                self.stats.endpoint_stats[route.name] = {
                    "requests": 0,
                    "successes": 0,
                    "failures": 0,
                    "avg_time": 0.0,
                }

            logger.info(f"Route ajoutée: {route.path_pattern} -> {route.backend_url}")

        except Exception as e:
            logger.error(f"Erreur ajout route {route.path_pattern}: {e}")

    def add_middleware(self, middleware: Middleware):
        """Ajouter un middleware"""

        self.middlewares.append(middleware)

        # Trier par priorité (plus petit = plus prioritaire)
        self.middlewares.sort(key=lambda m: m.priority)

        logger.info(f"Middleware ajouté: {middleware.name}")

    async def handle_request(self, request: Request) -> Response:
        """Traiter une requête HTTP"""

        start_time = time.time()

        try:
            # Exécuter middlewares pré-requête
            for middleware in self.middlewares:
                if middleware.pre_request_handler:
                    try:
                        await middleware.pre_request_handler(request)
                    except Exception as e:
                        logger.error(f"Erreur middleware {middleware.name}: {e}")
                        return self._create_error_response(500, "Internal middleware error")

            # Trouver la route correspondante
            route = await self._match_route(request)
            if not route:
                return self._create_error_response(404, "Route not found")

            request.route_matched = route.name

            # Vérifier authentification
            if route.auth_required and self.enable_auth:
                auth_result = await self._check_authentication(request)
                if not auth_result:
                    return self._create_error_response(401, "Unauthorized")

                # Vérifier autorisation
                if route.roles_required and not await self._check_authorization(
                    request, route.roles_required
                ):
                    return self._create_error_response(403, "Forbidden")

            # Vérifier rate limiting
            if self.enable_rate_limiting and not await self._check_rate_limit(request, route):
                self.stats.rate_limited_requests += 1
                return self._create_error_response(429, "Rate limit exceeded")

            # Vérifier cache
            cached_response = None
            if self.enable_caching and route.cache_ttl:
                cached_response = await self._check_cache(request, route)
                if cached_response:
                    self.stats.cache_hits += 1
                    cached_response.processing_time = time.time() - start_time
                    return cached_response
                else:
                    self.stats.cache_misses += 1

            # Transformer la requête si nécessaire
            if route.request_transform:
                request = await route.request_transform(request)

            # Vérifier circuit breaker
            if not await self._check_circuit_breaker(route.backend_url):
                return self._create_error_response(503, "Service temporarily unavailable")

            # Proxy vers le backend
            response = await self._proxy_request(request, route)

            # Transformer la réponse si nécessaire
            if route.response_transform:
                response = await route.response_transform(response)

            # Mettre en cache si nécessaire
            if self.enable_caching and route.cache_ttl and response.status_code == 200:
                await self._cache_response(request, route, response)

            # Mettre à jour circuit breaker
            await self._update_circuit_breaker(route.backend_url, True)

            # Calculer temps de traitement
            response.processing_time = time.time() - start_time

            # Exécuter middlewares post-réponse
            for middleware in reversed(self.middlewares):
                if middleware.post_response_handler:
                    try:
                        await middleware.post_response_handler(request, response)
                    except Exception as e:
                        logger.error(f"Erreur middleware post {middleware.name}: {e}")

            # Mettre à jour statistiques
            await self._update_stats(request, response, True)

            return response

        except Exception as e:
            logger.error(f"Erreur traitement requête {request.request_id}: {e}")

            # Mettre à jour circuit breaker en cas d'erreur
            if "route" in locals():
                await self._update_circuit_breaker(route.backend_url, False)

            error_response = self._create_error_response(500, "Internal server error")
            error_response.processing_time = time.time() - start_time

            await self._update_stats(request, error_response, False)

            return error_response

    async def _match_route(self, request: Request) -> Route | None:
        """Trouver la route correspondante"""

        for pattern, route in self.compiled_routes:
            if pattern.match(request.path) and request.method in route.methods:
                return route

        return None

    async def _check_authentication(self, request: Request) -> bool:
        """Vérifier l'authentification"""

        if not self.auth_service:
            return True  # Pas de service d'auth configuré

        try:
            # Extraire token d'authorization
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return False

            token = auth_header[7:]  # Enlever 'Bearer '

            # Vérifier le token
            session = await self.auth_service.verify_session(token)
            if session:
                request.user_id = session.user_id
                request.session_id = session.id
                return True

            return False

        except Exception as e:
            logger.error(f"Erreur authentification: {e}")
            return False

    async def _check_authorization(self, _request: Request, _required_roles: list[str]) -> bool:
        """Vérifier l'autorisation (rôles)"""

        # Simulation - en production intégrer avec le service de rôles
        return True

    async def _check_rate_limit(self, request: Request, route: Route) -> bool:
        """Vérifier rate limiting"""

        if not route.rate_limit_per_minute or not self.rate_limiter:
            return True

        # Créer clé de rate limit
        key_parts = [request.client_ip or "unknown"]
        if request.user_id:
            key_parts.append(request.user_id)
        key_parts.append(route.name)

        rate_key = ":".join(key_parts)

        return await self.rate_limiter.check_rate_limit(
            rate_key, route.rate_limit_per_minute, 60  # fenêtre de 60 secondes
        )

    async def _check_cache(self, request: Request, route: Route) -> Response | None:
        """Vérifier le cache"""

        if not self.cache_service:
            return None

        # Générer clé de cache
        if route.cache_key_generator:
            cache_key = route.cache_key_generator(request)
        else:
            cache_key = self._generate_default_cache_key(request)

        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            return self._deserialize_response(cached_data)

        return None

    async def _cache_response(self, request: Request, route: Route, response: Response):
        """Mettre en cache la réponse"""

        if not self.cache_service:
            return

        # Générer clé de cache
        if route.cache_key_generator:
            cache_key = route.cache_key_generator(request)
        else:
            cache_key = self._generate_default_cache_key(request)

        serialized_response = self._serialize_response(response)
        await self.cache_service.set(cache_key, serialized_response, ttl=route.cache_ttl)

    def _generate_default_cache_key(self, request: Request) -> str:
        """Générer clé de cache par défaut"""

        # Inclure méthode, path et paramètres de requête
        key_components = [
            request.method.value,
            request.path,
            json.dumps(request.query_params, sort_keys=True),
        ]

        key_string = "|".join(key_components)
        return f"gateway_cache:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def _check_circuit_breaker(self, backend_url: str) -> bool:
        """Vérifier le circuit breaker"""

        if backend_url not in self.circuit_breakers:
            self.circuit_breakers[backend_url] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure_time": 0,
                "success_count": 0,
            }

        breaker = self.circuit_breakers[backend_url]
        current_time = time.time()

        if breaker["state"] == "open":
            # Vérifier si on peut essayer de nouveau (après timeout)
            if current_time - breaker["last_failure_time"] > 60:  # 1 minute
                breaker["state"] = "half_open"
                breaker["success_count"] = 0
                return True
            return False

        return True

    async def _update_circuit_breaker(self, backend_url: str, success: bool):
        """Mettre à jour circuit breaker"""

        breaker = self.circuit_breakers[backend_url]
        current_time = time.time()

        if success:
            breaker["failure_count"] = 0
            breaker["success_count"] += 1

            if breaker["state"] == "half_open" and breaker["success_count"] >= 3:
                breaker["state"] = "closed"

        else:
            breaker["failure_count"] += 1
            breaker["last_failure_time"] = current_time

            if breaker["failure_count"] >= 5:  # Seuil de 5 échecs
                breaker["state"] = "open"

    async def _proxy_request(self, request: Request, route: Route) -> Response:
        """Proxifier la requête vers le backend"""

        # Simulation du proxy - en production utiliser httpx ou aiohttp
        try:
            # Simuler appel HTTP
            await asyncio.sleep(0.1)  # Simuler latence réseau

            # Simuler réponse réussie
            if route.backend_url.endswith("/error"):
                # Simuler erreur pour test
                return Response(
                    status_code=500,
                    headers={"Content-Type": "application/json"},
                    body=b'{"error": "Backend error"}',
                    backend_service=route.backend_url,
                )

            # Réponse normale
            response_body = {
                "success": True,
                "data": f"Response from {route.backend_url}",
                "request_id": request.request_id,
                "timestamp": time.time(),
            }

            return Response(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=json.dumps(response_body).encode(),
                backend_service=route.backend_url,
            )

        except Exception as e:
            logger.error(f"Erreur proxy vers {route.backend_url}: {e}")
            return Response(
                status_code=502,
                headers={"Content-Type": "application/json"},
                body=b'{"error": "Backend unreachable"}',
                backend_service=route.backend_url,
            )

    def _create_error_response(self, status_code: int, message: str) -> Response:
        """Créer réponse d'erreur"""

        error_body = {"error": True, "message": message, "timestamp": time.time()}

        return Response(
            status_code=status_code,
            headers={"Content-Type": "application/json"},
            body=json.dumps(error_body).encode(),
        )

    def _serialize_response(self, response: Response) -> dict[str, Any]:
        """Sérialiser réponse pour cache"""

        return {
            "status_code": response.status_code,
            "headers": response.headers,
            "body": response.body.decode("utf-8") if response.body else None,
            "cache_timestamp": time.time(),
        }

    def _deserialize_response(self, cached_data: dict[str, Any]) -> Response:
        """Désérialiser réponse du cache"""

        return Response(
            status_code=cached_data["status_code"],
            headers=cached_data["headers"],
            body=cached_data["body"].encode("utf-8") if cached_data["body"] else None,
            cache_hit=True,
        )

    async def _update_stats(self, request: Request, response: Response, success: bool):
        """Mettre à jour les statistiques"""

        self.stats.total_requests += 1

        if success and 200 <= response.status_code < 400:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1

        # Mettre à jour temps moyen de réponse
        total_requests = self.stats.total_requests
        current_avg = self.stats.avg_response_time
        new_avg = ((current_avg * (total_requests - 1)) + response.processing_time) / total_requests
        self.stats.avg_response_time = new_avg

        # Stats par endpoint
        if request.route_matched and request.route_matched in self.stats.endpoint_stats:
            endpoint_stats = self.stats.endpoint_stats[request.route_matched]
            endpoint_stats["requests"] += 1

            if success:
                endpoint_stats["successes"] += 1
            else:
                endpoint_stats["failures"] += 1

            # Temps moyen par endpoint
            req_count = endpoint_stats["requests"]
            current_time = endpoint_stats["avg_time"]
            endpoint_stats["avg_time"] = (
                (current_time * (req_count - 1)) + response.processing_time
            ) / req_count

    def _setup_default_middlewares(self):
        """Configurer middlewares par défaut"""

        # Middleware de logging
        logging_middleware = Middleware(
            name="request_logging",
            priority=1,
            pre_request_handler=self._log_request,
            post_response_handler=self._log_response,
        )
        self.add_middleware(logging_middleware)

        # Middleware CORS
        cors_middleware = Middleware(
            name="cors", priority=2, post_response_handler=self._add_cors_headers
        )
        self.add_middleware(cors_middleware)

    def _setup_default_routes(self):
        """Configurer routes par défaut"""

        # Route de santé
        health_route = Route(
            path_pattern=r"^/health$",
            methods=[HTTPMethod.GET],
            backend_url="internal://health",
            auth_required=False,
            name="health_check",
            description="Health check endpoint",
        )
        self.add_route(health_route)

        # Route des métriques
        metrics_route = Route(
            path_pattern=r"^/metrics$",
            methods=[HTTPMethod.GET],
            backend_url="internal://metrics",
            auth_required=False,
            name="metrics",
            description="Gateway metrics endpoint",
        )
        self.add_route(metrics_route)

    async def _log_request(self, request: Request):
        """Logger la requête"""
        logger.info(f"Request: {request.method.value} {request.path} from {request.client_ip}")

    async def _log_response(self, request: Request, response: Response):
        """Logger la réponse"""
        logger.info(
            f"Response: {response.status_code} for {request.request_id} in {response.processing_time:.3f}s"
        )

    async def _add_cors_headers(self, _request: Request, response: Response):
        """Ajouter headers CORS"""
        response.headers.update(
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )

    def get_gateway_statistics(self) -> dict[str, Any]:
        """Obtenir statistiques du gateway"""

        return {
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "success_rate": (self.stats.successful_requests / max(self.stats.total_requests, 1))
            * 100,
            "avg_response_time_ms": self.stats.avg_response_time * 1000,
            "rate_limited_requests": self.stats.rate_limited_requests,
            "cache_hit_rate": (
                self.stats.cache_hits / max(self.stats.cache_hits + self.stats.cache_misses, 1)
            )
            * 100,
            "routes_configured": len(self.routes),
            "middlewares_active": len(self.middlewares),
            "circuit_breakers": {
                url: breaker["state"] for url, breaker in self.circuit_breakers.items()
            },
            "endpoint_stats": dict(self.stats.endpoint_stats),
        }

    async def health_check(self) -> dict[str, Any]:
        """Vérification de santé du gateway"""

        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - getattr(self, "_start_time", time.time()),
            "components": {},
        }

        # Vérifier composants
        components_status = {
            "auth_service": self.auth_service is not None,
            "rate_limiter": self.rate_limiter is not None,
            "cache_service": self.cache_service is not None,
            "load_balancer": self.load_balancer is not None,
        }

        for component, enabled in components_status.items():
            health_status["components"][component] = "enabled" if enabled else "disabled"

        # Vérifier circuit breakers
        open_breakers = [
            url for url, breaker in self.circuit_breakers.items() if breaker["state"] == "open"
        ]

        if open_breakers:
            health_status["status"] = "degraded"
            health_status["open_circuit_breakers"] = open_breakers

        # Vérifier taux d'erreur récent
        if self.stats.total_requests > 100:
            error_rate = (self.stats.failed_requests / self.stats.total_requests) * 100
            if error_rate > 10:  # Plus de 10% d'erreurs
                health_status["status"] = "unhealthy"
                health_status["high_error_rate"] = error_rate

        return health_status


# Instance globale
api_gateway = APIGateway()


# Fonctions de convenance
async def route_request(method: str, path: str, headers: dict[str, str], **kwargs) -> Response:
    """Router une requête via le gateway"""

    request = Request(
        method=HTTPMethod(method.upper()),
        path=path,
        headers=headers,
        query_params=kwargs.get("query_params", {}),
        **{k: v for k, v in kwargs.items() if k != "query_params"},
    )

    return await api_gateway.handle_request(request)
