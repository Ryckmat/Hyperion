"""
Hyperion v3.0 - RBAC Engine
Moteur de contrôle d'accès basé sur les rôles
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class Role:
    name: str
    permissions: set[Permission]
    description: str = ""


class RBACEngine:
    """Moteur RBAC simple"""

    def __init__(self):
        self.roles: dict[str, Role] = {}
        self.user_roles: dict[str, set[str]] = {}

    def add_role(self, role: Role):
        """Ajoute un rôle"""
        self.roles[role.name] = role

    def assign_role(self, user_id: str, role_name: str):
        """Assigne un rôle à un utilisateur"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role_name)

    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Vérifie si l'utilisateur a la permission"""
        user_roles = self.user_roles.get(user_id, set())
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and permission in role.permissions:
                return True
        return False


# Instance globale
default_rbac_engine = RBACEngine()
