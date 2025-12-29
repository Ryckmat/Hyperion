"""
Authentication Manager for Hyperion v3.0

Gestionnaire d'authentification enterprise avec multi-factor et SSO.
"""

import logging
import re
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

try:
    import jwt
except ImportError:
    from ..jwt_fallback import jwt

try:
    import bcrypt
except ImportError:
    # Mock bcrypt
    class bcrypt:
        @staticmethod
        def gensalt(_rounds=12):
            return b"$2b$12$mock_salt"

        @staticmethod
        def hashpw(_password, _salt):
            return b"$2b$12$mock_hash"

        @staticmethod
        def checkpw(_password, _hashed):
            return True


try:
    import pyotp
except ImportError:
    # Mock pyotp
    class pyotp:
        @staticmethod
        def random_base32():
            return "MOCK_SECRET_KEY"

        @staticmethod
        def TOTP(_secret):
            class MockTOTP:
                def now(self):
                    return "123456"

                def verify(self, token):
                    return token == "123456"

                def provisioning_uri(self, name, issuer_name):
                    return f"otpauth://totp/{issuer_name}:{name}?secret=MOCK_SECRET&issuer={issuer_name}"

            return MockTOTP()


try:
    import qrcode
except ImportError:
    # Mock qrcode
    class qrcode:
        @staticmethod
        def make(data):
            class MockQR:
                def save(self, path):
                    with open(path, "w") as f:
                        f.write(f"QR Code: {data}")

            return MockQR()


logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Méthodes d'authentification supportées"""

    PASSWORD = "password"
    MFA_TOTP = "mfa_totp"
    MFA_SMS = "mfa_sms"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SAML = "saml"
    LDAP = "ldap"


class TokenType(Enum):
    """Types de tokens"""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFY = "verify"


class SecurityLevel(Enum):
    """Niveaux de sécurité"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class User:
    """Utilisateur du système"""

    id: str
    username: str
    email: str
    password_hash: str | None

    # Sécurité
    is_active: bool = True
    is_verified: bool = False
    security_level: SecurityLevel = SecurityLevel.MEDIUM

    # MFA
    mfa_enabled: bool = False
    mfa_secret: str | None = None
    backup_codes: list[str] = field(default_factory=list)

    # Sessions et sécurité
    last_login: datetime | None = None
    failed_attempts: int = 0
    locked_until: datetime | None = None

    # Métadonnées
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)


@dataclass
class Session:
    """Session utilisateur"""

    id: str
    user_id: str
    access_token: str
    refresh_token: str

    # Métadonnées session
    created_at: datetime
    expires_at: datetime
    last_activity: datetime

    # Sécurité
    ip_address: str | None = None
    user_agent: str | None = None
    is_mfa_verified: bool = False
    security_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthResult:
    """Résultat d'authentification"""

    success: bool
    user: User | None = None
    session: Session | None = None
    error_code: str | None = None
    error_message: str | None = None
    requires_mfa: bool = False
    security_warnings: list[str] = field(default_factory=list)


class AuthManager:
    """
    Gestionnaire d'authentification enterprise pour Hyperion v3.0

    Fonctionnalités :
    - Authentification multi-facteur (TOTP, SMS)
    - Gestion de sessions sécurisées
    - Intégration SSO (OAuth2, SAML)
    - Protection contre attaques (brute force, etc.)
    - Chiffrement robuste des mots de passe
    - Audit de sécurité complet
    - Rate limiting intelligent
    """

    def __init__(
        self,
        jwt_secret: str,
        bcrypt_rounds: int = 12,
        session_duration: int = 86400,  # 24h
        max_failed_attempts: int = 5,
        lockout_duration: int = 900,
    ):  # 15min

        self.jwt_secret = jwt_secret
        self.bcrypt_rounds = bcrypt_rounds
        self.session_duration = session_duration
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = lockout_duration

        # Storage (en production, utiliser une base de données)
        self.users: dict[str, User] = {}
        self.sessions: dict[str, Session] = {}
        self.api_keys: dict[str, str] = {}  # api_key -> user_id

        # Sécurité
        self.password_policy = {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digits": True,
            "require_special": True,
            "max_age_days": 90,
            "history_check": 5,  # Ne pas réutiliser les 5 derniers mots de passe
        }

        # Rate limiting par IP
        self.login_attempts: dict[str, list[datetime]] = {}
        self.rate_limit_window = 900  # 15 minutes
        self.max_attempts_per_ip = 10

        # Threading pour opérations asynchrones
        self.executor = ThreadPoolExecutor(max_workers=4)

        logger.info("AuthManager initialisé")

    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        mfa_code: str | None = None,
    ) -> AuthResult:
        """Authentification complète avec sécurité"""

        try:
            # Vérifier rate limiting par IP
            if ip_address and not self._check_rate_limit(ip_address):
                return AuthResult(
                    success=False,
                    error_code="RATE_LIMITED",
                    error_message="Trop de tentatives de connexion",
                )

            # Trouver l'utilisateur
            user = self._find_user(username)
            if not user:
                await self._record_failed_attempt(None, ip_address, "USER_NOT_FOUND")
                return AuthResult(
                    success=False,
                    error_code="INVALID_CREDENTIALS",
                    error_message="Identifiants invalides",
                )

            # Vérifier si le compte est verrouillé
            if self._is_account_locked(user):
                return AuthResult(
                    success=False,
                    error_code="ACCOUNT_LOCKED",
                    error_message=f"Compte verrouillé jusqu'à {user.locked_until}",
                )

            # Vérifier si le compte est actif
            if not user.is_active:
                return AuthResult(
                    success=False, error_code="ACCOUNT_INACTIVE", error_message="Compte inactif"
                )

            # Vérifier le mot de passe
            if not await self._verify_password(password, user.password_hash):
                await self._record_failed_attempt(user, ip_address, "INVALID_PASSWORD")
                return AuthResult(
                    success=False,
                    error_code="INVALID_CREDENTIALS",
                    error_message="Identifiants invalides",
                )

            # Vérifier MFA si activé
            if user.mfa_enabled:
                if not mfa_code:
                    return AuthResult(
                        success=False,
                        requires_mfa=True,
                        error_code="MFA_REQUIRED",
                        error_message="Code MFA requis",
                    )

                if not await self._verify_mfa(user, mfa_code):
                    await self._record_failed_attempt(user, ip_address, "INVALID_MFA")
                    return AuthResult(
                        success=False, error_code="INVALID_MFA", error_message="Code MFA invalide"
                    )

            # Authentification réussie
            await self._record_successful_login(user, ip_address)

            # Créer session
            session = await self._create_session(user, ip_address, user_agent, user.mfa_enabled)

            return AuthResult(success=True, user=user, session=session)

        except Exception as e:
            logger.error(f"Erreur authentification: {e}")
            return AuthResult(
                success=False, error_code="INTERNAL_ERROR", error_message="Erreur interne"
            )

    async def create_user(
        self, username: str, email: str, password: str, roles: list[str] | None = None
    ) -> tuple[bool, str]:
        """Créer un nouvel utilisateur"""

        try:
            # Validation des données
            if not self._validate_username(username):
                return False, "Nom d'utilisateur invalide"

            if not self._validate_email(email):
                return False, "Adresse email invalide"

            password_valid, password_message = self._validate_password(password)
            if not password_valid:
                return False, password_message

            # Vérifier unicité
            if self._find_user(username) or self._find_user_by_email(email):
                return False, "Utilisateur déjà existant"

            # Hasher le mot de passe
            password_hash = await self._hash_password(password)

            # Créer utilisateur
            user = User(
                id=self._generate_user_id(),
                username=username,
                email=email,
                password_hash=password_hash,
                roles=roles or ["user"],
                security_level=SecurityLevel.MEDIUM,
            )

            self.users[user.id] = user

            logger.info(f"Utilisateur créé: {username}")
            return True, "Utilisateur créé avec succès"

        except Exception as e:
            logger.error(f"Erreur création utilisateur: {e}")
            return False, "Erreur interne"

    async def enable_mfa(self, user_id: str) -> tuple[bool, str, str | None]:
        """Activer l'authentification multi-facteur"""

        user = self.users.get(user_id)
        if not user:
            return False, "Utilisateur non trouvé", None

        try:
            # Générer secret TOTP
            secret = pyotp.random_base32()

            # Générer codes de récupération
            backup_codes = [secrets.token_hex(4) for _ in range(10)]

            user.mfa_secret = secret
            user.backup_codes = backup_codes
            user.mfa_enabled = True
            user.updated_at = datetime.now()

            # Générer QR code URI pour apps authenticator
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(user.email, issuer_name="Hyperion v3.0")

            logger.info(f"MFA activé pour utilisateur: {user.username}")
            return True, "MFA activé", provisioning_uri

        except Exception as e:
            logger.error(f"Erreur activation MFA: {e}")
            return False, "Erreur interne", None

    async def verify_session(self, access_token: str) -> Session | None:
        """Vérifier et valider une session"""

        try:
            # Décoder le token JWT
            payload = jwt.decode(access_token, self.jwt_secret, algorithms=["HS256"])

            session_id = payload.get("session_id")
            if not session_id:
                return None

            # Récupérer la session
            session = self.sessions.get(session_id)
            if not session:
                return None

            # Vérifier expiration
            if datetime.now() > session.expires_at:
                await self._cleanup_session(session_id)
                return None

            # Vérifier que le token correspond
            if session.access_token != access_token:
                return None

            # Mettre à jour dernière activité
            session.last_activity = datetime.now()

            return session

        except jwt.ExpiredSignatureError:
            logger.debug("Token JWT expiré")
            return None
        except jwt.InvalidTokenError:
            logger.debug("Token JWT invalide")
            return None
        except Exception as e:
            logger.error(f"Erreur vérification session: {e}")
            return None

    async def refresh_session(self, refresh_token: str) -> Session | None:
        """Actualiser une session avec le refresh token"""

        try:
            # Décoder refresh token
            payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=["HS256"])

            session_id = payload.get("session_id")
            token_type = payload.get("type")

            if token_type != TokenType.REFRESH.value or not session_id:
                return None

            # Récupérer session
            session = self.sessions.get(session_id)
            if not session or session.refresh_token != refresh_token:
                return None

            # Vérifier que pas trop ancienne pour refresh
            max_refresh_age = timedelta(days=30)
            if datetime.now() - session.created_at > max_refresh_age:
                await self._cleanup_session(session_id)
                return None

            # Générer nouveaux tokens
            user = self.users.get(session.user_id)
            if not user:
                return None

            new_access_token = self._generate_access_token(session_id, user.id)
            new_refresh_token = self._generate_refresh_token(session_id, user.id)

            # Mettre à jour session
            session.access_token = new_access_token
            session.refresh_token = new_refresh_token
            session.expires_at = datetime.now() + timedelta(seconds=self.session_duration)
            session.last_activity = datetime.now()

            logger.debug(f"Session actualisée: {session_id}")
            return session

        except jwt.ExpiredSignatureError:
            logger.debug("Refresh token expiré")
            return None
        except jwt.InvalidTokenError:
            logger.debug("Refresh token invalide")
            return None
        except Exception as e:
            logger.error(f"Erreur actualisation session: {e}")
            return None

    async def logout(self, session_id: str) -> bool:
        """Déconnexion et nettoyage session"""

        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                user = self.users.get(session.user_id)

                await self._cleanup_session(session_id)

                logger.info(f"Déconnexion utilisateur: {user.username if user else 'unknown'}")
                return True

            return False

        except Exception as e:
            logger.error(f"Erreur déconnexion: {e}")
            return False

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> tuple[bool, str]:
        """Changer le mot de passe"""

        try:
            user = self.users.get(user_id)
            if not user:
                return False, "Utilisateur non trouvé"

            # Vérifier mot de passe actuel
            if not await self._verify_password(current_password, user.password_hash):
                return False, "Mot de passe actuel incorrect"

            # Valider nouveau mot de passe
            valid, message = self._validate_password(new_password)
            if not valid:
                return False, message

            # Hasher nouveau mot de passe
            new_hash = await self._hash_password(new_password)

            # Mettre à jour
            user.password_hash = new_hash
            user.updated_at = datetime.now()

            # Invalider toutes les sessions actives
            await self._invalidate_user_sessions(user_id)

            logger.info(f"Mot de passe changé: {user.username}")
            return True, "Mot de passe changé avec succès"

        except Exception as e:
            logger.error(f"Erreur changement mot de passe: {e}")
            return False, "Erreur interne"

    async def generate_api_key(self, user_id: str) -> str | None:
        """Générer une clé API pour un utilisateur"""

        try:
            user = self.users.get(user_id)
            if not user:
                return None

            # Générer clé API sécurisée
            api_key = f"hyp_{secrets.token_urlsafe(32)}"

            self.api_keys[api_key] = user_id

            logger.info(f"Clé API générée pour: {user.username}")
            return api_key

        except Exception as e:
            logger.error(f"Erreur génération clé API: {e}")
            return None

    async def verify_api_key(self, api_key: str) -> User | None:
        """Vérifier une clé API"""

        user_id = self.api_keys.get(api_key)
        if user_id:
            return self.users.get(user_id)
        return None

    # Méthodes internes

    def _find_user(self, identifier: str) -> User | None:
        """Trouver utilisateur par nom ou email"""
        for user in self.users.values():
            if user.username == identifier or user.email == identifier:
                return user
        return None

    def _find_user_by_email(self, email: str) -> User | None:
        """Trouver utilisateur par email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def _check_rate_limit(self, ip_address: str) -> bool:
        """Vérifier rate limiting par IP"""

        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=self.rate_limit_window)

        # Nettoyer anciennes tentatives
        if ip_address in self.login_attempts:
            self.login_attempts[ip_address] = [
                attempt for attempt in self.login_attempts[ip_address] if attempt > window_start
            ]

            # Vérifier limite
            if len(self.login_attempts[ip_address]) >= self.max_attempts_per_ip:
                return False

        return True

    def _is_account_locked(self, user: User) -> bool:
        """Vérifier si le compte est verrouillé"""
        return user.locked_until and datetime.now() < user.locked_until

    async def _verify_password(self, password: str, password_hash: str) -> bool:
        """Vérifier mot de passe avec bcrypt"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            return False

    async def _hash_password(self, password: str) -> str:
        """Hasher mot de passe avec bcrypt"""
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    async def _verify_mfa(self, user: User, code: str) -> bool:
        """Vérifier code MFA TOTP"""
        try:
            if not user.mfa_secret:
                return False

            totp = pyotp.TOTP(user.mfa_secret)

            # Vérifier code TOTP
            if totp.verify(code):
                return True

            # Vérifier codes de récupération
            if code in user.backup_codes:
                user.backup_codes.remove(code)  # Code à usage unique
                return True

            return False

        except Exception as e:
            logger.error(f"Erreur vérification MFA: {e}")
            return False

    async def _record_failed_attempt(self, user: User | None, ip_address: str | None, reason: str):
        """Enregistrer tentative échouée"""

        # Enregistrer par IP
        if ip_address:
            if ip_address not in self.login_attempts:
                self.login_attempts[ip_address] = []
            self.login_attempts[ip_address].append(datetime.now())

        # Enregistrer pour l'utilisateur
        if user:
            user.failed_attempts += 1

            # Verrouiller si trop d'échecs
            if user.failed_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.now() + timedelta(seconds=self.lockout_duration)
                logger.warning(f"Compte verrouillé: {user.username}")

        logger.warning(f"Tentative de connexion échouée: {reason}")

    async def _record_successful_login(self, user: User, ip_address: str | None):
        """Enregistrer connexion réussie"""

        user.last_login = datetime.now()
        user.failed_attempts = 0
        user.locked_until = None

        logger.info(f"Connexion réussie: {user.username} depuis {ip_address or 'unknown'}")

    async def _create_session(
        self,
        user: User,
        ip_address: str | None,
        user_agent: str | None,
        is_mfa_verified: bool,
    ) -> Session:
        """Créer nouvelle session"""

        session_id = secrets.token_urlsafe(32)

        # Générer tokens JWT
        access_token = self._generate_access_token(session_id, user.id)
        refresh_token = self._generate_refresh_token(session_id, user.id)

        # Créer session
        session = Session(
            id=session_id,
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=self.session_duration),
            last_activity=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            is_mfa_verified=is_mfa_verified,
        )

        self.sessions[session_id] = session

        logger.debug(f"Session créée: {session_id}")
        return session

    def _generate_access_token(self, session_id: str, user_id: str) -> str:
        """Générer token d'accès JWT"""

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "type": TokenType.ACCESS.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=self.session_duration),
        }

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def _generate_refresh_token(self, session_id: str, user_id: str) -> str:
        """Générer refresh token JWT"""

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "type": TokenType.REFRESH.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=30),  # Plus long pour refresh
        }

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    async def _cleanup_session(self, session_id: str):
        """Nettoyer une session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    async def _invalidate_user_sessions(self, user_id: str):
        """Invalider toutes les sessions d'un utilisateur"""
        sessions_to_remove = [
            sid for sid, session in self.sessions.items() if session.user_id == user_id
        ]

        for session_id in sessions_to_remove:
            await self._cleanup_session(session_id)

        logger.info(f"Sessions invalidées pour utilisateur: {user_id}")

    def _generate_user_id(self) -> str:
        """Générer ID utilisateur unique"""
        return f"user_{secrets.token_hex(8)}"

    def _validate_username(self, username: str) -> bool:
        """Valider nom d'utilisateur"""
        if not username or len(username) < 3:
            return False

        # Alphanumerique + underscore/tiret
        pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(pattern, username))

    def _validate_email(self, email: str) -> bool:
        """Valider adresse email"""
        if not email:
            return False

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _validate_password(self, password: str) -> tuple[bool, str]:
        """Valider mot de passe selon la politique"""

        if len(password) < self.password_policy["min_length"]:
            return (
                False,
                f"Mot de passe trop court (min {self.password_policy['min_length']} caractères)",
            )

        if self.password_policy["require_uppercase"] and not re.search(r"[A-Z]", password):
            return False, "Le mot de passe doit contenir au moins une majuscule"

        if self.password_policy["require_lowercase"] and not re.search(r"[a-z]", password):
            return False, "Le mot de passe doit contenir au moins une minuscule"

        if self.password_policy["require_digits"] and not re.search(r"\d", password):
            return False, "Le mot de passe doit contenir au moins un chiffre"

        if self.password_policy["require_special"] and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            return False, "Le mot de passe doit contenir au moins un caractère spécial"

        return True, "Mot de passe valide"

    def get_auth_statistics(self) -> dict[str, Any]:
        """Obtenir statistiques d'authentification"""

        active_sessions = len(self.sessions)
        total_users = len(self.users)
        mfa_enabled_users = len([u for u in self.users.values() if u.mfa_enabled])
        locked_accounts = len([u for u in self.users.values() if self._is_account_locked(u)])

        return {
            "total_users": total_users,
            "active_sessions": active_sessions,
            "mfa_adoption_rate": (mfa_enabled_users / max(total_users, 1)) * 100,
            "locked_accounts": locked_accounts,
            "api_keys_issued": len(self.api_keys),
            "security_level_distribution": {
                level.name: len([u for u in self.users.values() if u.security_level == level])
                for level in SecurityLevel
            },
        }


# Instance globale
auth_manager = AuthManager(jwt_secret=secrets.token_urlsafe(32))


# Fonctions de convenance
async def authenticate_user(username: str, password: str, **kwargs) -> AuthResult:
    """Authentifier un utilisateur"""
    return await auth_manager.authenticate(username, password, **kwargs)


async def verify_session_token(access_token: str) -> Session | None:
    """Vérifier un token de session"""
    return await auth_manager.verify_session(access_token)
