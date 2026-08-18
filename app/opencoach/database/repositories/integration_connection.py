from abc import ABC, abstractmethod
from uuid import UUID

from opencoach.models import IntegrationConnection


class IntegrationConnectionRepository(ABC):
    """Abstraction de persistance des connexions externes."""

    @abstractmethod
    def get_connection(
        self,
        athlete_profile_id: UUID,
        provider: str,
    ) -> IntegrationConnection | None:
        """Retourne une connexion configurée."""
        raise NotImplementedError

    @abstractmethod
    def save_connection(
        self,
        athlete_profile_id: UUID,
        connection: IntegrationConnection,
        encrypted_secret: bytes | None,
    ) -> None:
        """Crée ou met à jour une connexion."""
        raise NotImplementedError

    @abstractmethod
    def get_encrypted_secret(
        self,
        athlete_profile_id: UUID,
        provider: str,
    ) -> bytes | None:
        """Retourne le secret chiffré d'une connexion."""
        raise NotImplementedError
