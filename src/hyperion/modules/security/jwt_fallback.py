"""
JWT Fallback pour tests sans dépendances
"""

import base64
import hashlib
import hmac
import json
import time


class jwt:
    @staticmethod
    def encode(payload, key, algorithm="HS256"):
        """Mock JWT encode"""
        header = {"typ": "JWT", "alg": algorithm}

        # Encoder header et payload en base64
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

        # Créer signature simple
        message = f"{header_b64}.{payload_b64}"
        signature = (
            base64.urlsafe_b64encode(
                hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()
            )
            .decode()
            .rstrip("=")
        )

        return f"{header_b64}.{payload_b64}.{signature}"

    @staticmethod
    def decode(token, _key, _algorithms=None):
        """Mock JWT decode"""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise Exception("Invalid token format")

            # Décoder le payload
            payload_part = parts[1]
            # Ajouter padding si nécessaire
            payload_part += "=" * (4 - len(payload_part) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_part))

            # Vérifier expiration
            if "exp" in payload and payload["exp"] < time.time():
                raise Exception("Token expired")

            return payload
        except Exception as e:
            raise Exception(f"Invalid token: {e}") from e

    class InvalidTokenError(Exception):
        pass

    class ExpiredSignatureError(Exception):
        pass
