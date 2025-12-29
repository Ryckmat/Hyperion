"""
Hyperion v3.0 - Request Router
Routeur de requêtes intelligent pour l'API Gateway
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


@dataclass
class RouteMatch:
    """Résultat d'un match de route"""

    route_id: str
    path_params: dict[str, str]
    backend_url: str
    priority: int


class RequestRouter:
    """Routeur de requêtes intelligent"""

    def __init__(self):
        self.routes: dict[str, dict] = {}
        self.patterns: list[dict] = []

    def add_route(
        self, route_id: str, pattern: str, backend: str, methods: list[HTTPMethod] = None
    ):
        """Ajoute une route"""
        if methods is None:
            methods = [HTTPMethod.GET]

        route_config = {
            "pattern": pattern,
            "backend": backend,
            "methods": [m.value for m in methods],
            "regex": re.compile(pattern),
        }

        self.routes[route_id] = route_config
        self.patterns.append({"id": route_id, "config": route_config})
        logger.info(f"Route ajoutée: {route_id} -> {pattern}")

    def route_request(self, path: str, method: str) -> RouteMatch | None:
        """Route une requête vers le bon backend"""
        for route in self.patterns:
            config = route["config"]

            if method not in config["methods"]:
                continue

            match = config["regex"].match(path)
            if match:
                return RouteMatch(
                    route_id=route["id"],
                    path_params=match.groupdict(),
                    backend_url=config["backend"],
                    priority=1,
                )

        return None

    def get_route_stats(self) -> dict[str, Any]:
        """Retourne les statistiques de routage"""
        return {"total_routes": len(self.routes), "routes": list(self.routes.keys())}


# Instance globale
default_request_router = RequestRouter()
