import json
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

from opencoach.database.repositories import (
    IntegrationConnectionRepository,
)
from opencoach.models import IntegrationConnection
from opencoach.security import SecretCipher


class IntegrationConnectionServiceError(RuntimeError):
    """Erreur métier liée aux connexions externes."""


@dataclass(frozen=True)
class IntegrationCredentials:
    """Credentials déchiffrés utilisés uniquement côté backend."""

    provider: str
    athlete_id: str
    secret: str
    web_cookie: str | None = None


class IntegrationConnectionService:
    """Gère les connexions vers les services externes."""

    def __init__(
        self,
        repository: IntegrationConnectionRepository,
        cipher: SecretCipher,
    ) -> None:
        self.repository = repository
        self.cipher = cipher

    def get_connection(
        self,
        athlete_profile_id: UUID,
        provider: str,
    ) -> IntegrationConnection | None:
        return self.repository.get_connection(
            athlete_profile_id,
            provider,
        )

    def _decode_intervals_secret(
        self,
        encrypted_secret: bytes | None,
    ) -> dict[str, str | None]:
        if encrypted_secret is None:
            return {"api_key": None, "web_cookie": None}

        decrypted = self.cipher.decrypt(encrypted_secret)
        try:
            payload = json.loads(decrypted)
        except (TypeError, ValueError):
            # Compatibilité avec les anciennes connexions qui stockaient
            # directement la clé API, sans enveloppe JSON.
            return {"api_key": decrypted, "web_cookie": None}

        if not isinstance(payload, dict):
            return {"api_key": decrypted, "web_cookie": None}

        return {
            "api_key": payload.get("api_key"),
            "web_cookie": payload.get("web_cookie"),
        }

    def has_intervals_web_cookie(
        self,
        athlete_profile_id: UUID,
    ) -> bool:
        encrypted_secret = self.repository.get_encrypted_secret(
            athlete_profile_id,
            "intervals",
        )
        return bool(
            self._decode_intervals_secret(encrypted_secret).get("web_cookie")
        )

    def save_intervals_connection(
        self,
        athlete_profile_id: UUID,
        athlete_id: str,
        api_key: str | None,
        *,
        web_cookie: str | None = None,
        enabled: bool = True,
    ) -> IntegrationConnection:
        normalized_athlete_id = athlete_id.strip()

        if not normalized_athlete_id:
            raise IntegrationConnectionServiceError(
                "L'identifiant athlète Intervals.icu est obligatoire."
            )

        current = self.repository.get_connection(
            athlete_profile_id,
            "intervals",
        )
        current_secret = self.repository.get_encrypted_secret(
            athlete_profile_id,
            "intervals",
        )
        secrets = self._decode_intervals_secret(current_secret)

        if api_key is not None:
            normalized_api_key = api_key.strip()
            if not normalized_api_key:
                raise IntegrationConnectionServiceError(
                    "La clé API Intervals.icu ne peut pas être vide."
                )
            secrets["api_key"] = normalized_api_key

        if web_cookie is not None:
            normalized_cookie = web_cookie.strip()
            secrets["web_cookie"] = normalized_cookie or None

        if not secrets.get("api_key"):
            raise IntegrationConnectionServiceError(
                "La clé API Intervals.icu est obligatoire."
            )

        encrypted_secret = self.cipher.encrypt(
            json.dumps(secrets, separators=(",", ":")),
        )

        connection = IntegrationConnection(
            provider="intervals",
            enabled=enabled,
            athlete_id=normalized_athlete_id,
            secret_configured=True,
        )

        self.repository.save_connection(
            athlete_profile_id,
            connection,
            encrypted_secret,
        )

        return connection

    def get_credentials(
        self,
        athlete_profile_id: UUID,
        provider: str,
    ) -> IntegrationCredentials:
        connection = self.repository.get_connection(
            athlete_profile_id,
            provider,
        )

        if connection is None:
            raise IntegrationConnectionServiceError(
                f"L'intégration '{provider}' n'est pas configurée."
            )

        if not connection.enabled:
            raise IntegrationConnectionServiceError(
                f"L'intégration '{provider}' est désactivée."
            )

        if not connection.athlete_id:
            raise IntegrationConnectionServiceError(
                f"L'intégration '{provider}' est incomplète."
            )

        encrypted_secret = self.repository.get_encrypted_secret(
            athlete_profile_id,
            provider,
        )

        if encrypted_secret is None:
            raise IntegrationConnectionServiceError(
                f"Le secret de l'intégration '{provider}' est absent."
            )

        secrets = self._decode_intervals_secret(encrypted_secret)
        secret = secrets.get("api_key")
        if not secret:
            raise IntegrationConnectionServiceError(
                f"La clé API de l'intégration '{provider}' est absente."
            )

        return IntegrationCredentials(
            provider=provider,
            athlete_id=connection.athlete_id,
            secret=secret,
            web_cookie=secrets.get("web_cookie"),
        )

    def mark_synced(
        self,
        athlete_profile_id: UUID,
        provider: str,
        synced_at: datetime,
    ) -> None:
        self.repository.mark_synced(
            athlete_profile_id,
            provider,
            synced_at,
        )
