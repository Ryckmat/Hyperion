"""
Hyperion v3.0 - Service de Chiffrement Enterprise
Service de chiffrement et déchiffrement pour données sensibles
"""

import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


@dataclass
class EncryptionResult:
    """Résultat du chiffrement"""

    encrypted_data: bytes
    salt: bytes
    algorithm: str
    key_id: str | None = None


@dataclass
class EncryptionConfig:
    """Configuration du service de chiffrement"""

    default_algorithm: str = "fernet"
    key_rotation_enabled: bool = True
    salt_length: int = 32
    iterations: int = 100000


class EncryptionService:
    """Service de chiffrement enterprise avec rotation des clés"""

    def __init__(self, config: EncryptionConfig = None):
        self.config = config or EncryptionConfig()
        self.master_key: bytes | None = None
        self.keys_cache: dict[str, Fernet] = {}
        self.current_key_id = "default"

        # Initialisation avec clé par défaut
        self._initialize_default_key()

    def _initialize_default_key(self):
        """Initialise une clé par défaut pour les tests"""
        try:
            # Générer une clé déterministe pour les tests
            test_password = b"hyperion_test_password_v3_enterprise"
            salt = b"hyperion_default_salt_for_testing_2024"

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.config.iterations,
            )

            key = base64.urlsafe_b64encode(kdf.derive(test_password))
            self.master_key = key
            self.keys_cache[self.current_key_id] = Fernet(key)

            logger.info(f"Service de chiffrement initialisé avec clé {self.current_key_id}")

        except Exception as e:
            logger.error(f"Erreur initialisation service chiffrement: {e}")
            # Fallback avec clé générée aléatoirement
            self.master_key = Fernet.generate_key()
            self.keys_cache[self.current_key_id] = Fernet(self.master_key)

    def set_master_key(self, password: str | bytes, salt: bytes | None = None) -> str:
        """Configure la clé maître à partir d'un mot de passe"""
        try:
            if isinstance(password, str):
                password = password.encode("utf-8")

            if salt is None:
                salt = secrets.token_bytes(self.config.salt_length)

            # Dérivation de clé avec PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.config.iterations,
            )

            key = base64.urlsafe_b64encode(kdf.derive(password))
            key_id = hashlib.sha256(key).hexdigest()[:16]

            self.master_key = key
            self.keys_cache[key_id] = Fernet(key)
            self.current_key_id = key_id

            logger.info(f"Clé maître configurée avec ID: {key_id}")
            return key_id

        except Exception as e:
            logger.error(f"Erreur configuration clé maître: {e}")
            raise

    def encrypt(self, data: str | bytes, key_id: str | None = None) -> EncryptionResult:
        """Chiffre des données"""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            # Utiliser la clé spécifiée ou celle par défaut
            target_key_id = key_id or self.current_key_id

            if target_key_id not in self.keys_cache:
                raise ValueError(f"Clé non trouvée: {target_key_id}")

            fernet = self.keys_cache[target_key_id]
            encrypted_data = fernet.encrypt(data)

            # Générer un salt pour cette opération
            salt = secrets.token_bytes(self.config.salt_length)

            result = EncryptionResult(
                encrypted_data=encrypted_data,
                salt=salt,
                algorithm=self.config.default_algorithm,
                key_id=target_key_id,
            )

            logger.debug(f"Données chiffrées avec clé {target_key_id}")
            return result

        except Exception as e:
            logger.error(f"Erreur chiffrement: {e}")
            raise

    def decrypt(self, encrypted_result: EncryptionResult) -> bytes:
        """Déchiffre des données"""
        try:
            key_id = encrypted_result.key_id or self.current_key_id

            if key_id not in self.keys_cache:
                raise ValueError(f"Clé non trouvée pour déchiffrement: {key_id}")

            fernet = self.keys_cache[key_id]
            decrypted_data = fernet.decrypt(encrypted_result.encrypted_data)

            logger.debug(f"Données déchiffrées avec clé {key_id}")
            return decrypted_data

        except Exception as e:
            logger.error(f"Erreur déchiffrement: {e}")
            raise

    def decrypt_raw(self, encrypted_data: bytes, key_id: str | None = None) -> bytes:
        """Déchiffre des données brutes"""
        try:
            target_key_id = key_id or self.current_key_id

            if target_key_id not in self.keys_cache:
                raise ValueError(f"Clé non trouvée: {target_key_id}")

            fernet = self.keys_cache[target_key_id]
            return fernet.decrypt(encrypted_data)

        except Exception as e:
            logger.error(f"Erreur déchiffrement brut: {e}")
            raise

    def encrypt_string(self, text: str, key_id: str | None = None) -> str:
        """Chiffre une chaîne et retourne une chaîne encodée en base64"""
        try:
            result = self.encrypt(text, key_id)
            # Encoder le résultat en base64 pour stockage/transport
            encoded = base64.b64encode(result.encrypted_data).decode("utf-8")
            return encoded

        except Exception as e:
            logger.error(f"Erreur chiffrement chaîne: {e}")
            raise

    def decrypt_string(self, encrypted_text: str, key_id: str | None = None) -> str:
        """Déchiffre une chaîne encodée en base64"""
        try:
            # Décoder depuis base64
            encrypted_data = base64.b64decode(encrypted_text.encode("utf-8"))
            decrypted_bytes = self.decrypt_raw(encrypted_data, key_id)
            return decrypted_bytes.decode("utf-8")

        except Exception as e:
            logger.error(f"Erreur déchiffrement chaîne: {e}")
            raise

    def rotate_key(self) -> str:
        """Effectue une rotation de clé"""
        try:
            # Générer une nouvelle clé
            new_key = Fernet.generate_key()
            new_key_id = hashlib.sha256(new_key).hexdigest()[:16]

            # Ajouter au cache
            self.keys_cache[new_key_id] = Fernet(new_key)

            # Marquer comme clé courante
            old_key_id = self.current_key_id
            self.current_key_id = new_key_id

            logger.info(f"Rotation de clé effectuée: {old_key_id} -> {new_key_id}")
            return new_key_id

        except Exception as e:
            logger.error(f"Erreur rotation de clé: {e}")
            raise

    def hash_password(self, password: str, salt: bytes | None = None) -> dict[str, Any]:
        """Hache un mot de passe avec salt"""
        try:
            if salt is None:
                salt = secrets.token_bytes(32)

            # Utiliser PBKDF2 pour le hachage
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.config.iterations,
            )

            password_hash = kdf.derive(password.encode("utf-8"))

            return {
                "hash": base64.b64encode(password_hash).decode("utf-8"),
                "salt": base64.b64encode(salt).decode("utf-8"),
                "algorithm": "pbkdf2_sha256",
                "iterations": self.config.iterations,
            }

        except Exception as e:
            logger.error(f"Erreur hachage mot de passe: {e}")
            raise

    def verify_password(self, password: str, password_data: dict[str, Any]) -> bool:
        """Vérifie un mot de passe contre son hachage"""
        try:
            salt = base64.b64decode(password_data["salt"])
            stored_hash = base64.b64decode(password_data["hash"])
            iterations = password_data.get("iterations", self.config.iterations)

            # Recalculer le hachage
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations,
            )

            calculated_hash = kdf.derive(password.encode("utf-8"))

            # Comparaison sécurisée
            return secrets.compare_digest(stored_hash, calculated_hash)

        except Exception as e:
            logger.error(f"Erreur vérification mot de passe: {e}")
            return False

    def get_key_info(self) -> dict[str, Any]:
        """Retourne des informations sur les clés"""
        return {
            "current_key_id": self.current_key_id,
            "total_keys": len(self.keys_cache),
            "available_keys": list(self.keys_cache.keys()),
            "rotation_enabled": self.config.key_rotation_enabled,
        }

    def secure_delete_key(self, key_id: str) -> bool:
        """Supprime une clé de manière sécurisée"""
        try:
            if key_id == self.current_key_id:
                raise ValueError("Impossible de supprimer la clé courante")

            if key_id in self.keys_cache:
                del self.keys_cache[key_id]
                logger.info(f"Clé supprimée de manière sécurisée: {key_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Erreur suppression clé: {e}")
            return False


class AdvancedEncryptionService(EncryptionService):
    """Service de chiffrement avancé avec fonctionnalités enterprise"""

    def __init__(self, config: EncryptionConfig = None):
        super().__init__(config)
        self.audit_log = []

    def encrypt_with_audit(self, data: str | bytes, context: str = "unknown") -> EncryptionResult:
        """Chiffrement avec audit trail"""
        try:
            result = self.encrypt(data)

            # Enregistrer dans l'audit
            audit_entry = {
                "timestamp": (
                    logger._get_current_time()
                    if hasattr(logger, "_get_current_time")
                    else "unknown"
                ),
                "operation": "encrypt",
                "key_id": result.key_id,
                "context": context,
                "data_size": len(data) if isinstance(data, (str, bytes)) else 0,
            }
            self.audit_log.append(audit_entry)

            return result

        except Exception as e:
            logger.error(f"Erreur chiffrement avec audit: {e}")
            raise

    def get_audit_log(self) -> list:
        """Retourne l'audit trail"""
        return self.audit_log.copy()


# Instances globales pour l'enterprise
default_encryption_service = EncryptionService()
advanced_encryption_service = AdvancedEncryptionService()


# Fonctions utilitaires pour compatibilité
def encrypt_data(data: str | bytes) -> str:
    """Fonction utilitaire pour chiffrement simple"""
    return default_encryption_service.encrypt_string(str(data))


def decrypt_data(encrypted_data: str) -> str:
    """Fonction utilitaire pour déchiffrement simple"""
    return default_encryption_service.decrypt_string(encrypted_data)


def hash_sensitive_data(data: str) -> str:
    """Hache des données sensibles"""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
