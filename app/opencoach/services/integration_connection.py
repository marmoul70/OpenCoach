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

    def save_intervals_connection(
        self,
        athlete_profile_id: UUID,
        athlete_id: str,
        api_key: str | None,
        *,
        enabled: bool = True,
    ) -> IntegrationConnection:
        normalized_athlete_id = athlete_id.strip()

        if not normalized_athlete_id:
            raise IntegrationConnectionServiceError(
                "L'identifiant athlète Intervals.icu est obligatoire."
            )

        encrypted_secret: bytes | None = None

        if api_key is not None:
            normalized_api_key = api_key.strip()

            if not normalized_api_key:
                raise IntegrationConnectionServiceError(
                    "La clé API Intervals.icu ne peut pas être vide."
                )

            encrypted_secret = self.cipher.encrypt(
                normalized_api_key,
            )

        current = self.repository.get_connection(
            athlete_profile_id,
            "intervals",
        )

        if current is None and encrypted_secret is None:
            raise IntegrationConnectionServiceError(
                "La clé API Intervals.icu est obligatoire."
            )

        connection = IntegrationConnection(
            provider="intervals",
            enabled=enabled,
            athlete_id=normalized_athlete_id,
            secret_configured=(
                encrypted_secret is not None
                or (
                    current is not None
                    and current.secret_configured
                )
            ),
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

        secret = self.cipher.decrypt(
            encrypted_secret,
        )

        return IntegrationCredentials(
            provider=provider,
            athlete_id=connection.athlete_id,
            secret=secret,
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
