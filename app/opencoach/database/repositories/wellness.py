from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from opencoach.models import WellnessDay


class WellnessRepository(ABC):
    """Abstraction de persistance des données Wellness."""

    @abstractmethod
    def save_wellness_day(
        self,
        athlete_profile_id: UUID,
        wellness: WellnessDay,
    ) -> None:
        """Crée ou met à jour une journée Wellness."""
        raise NotImplementedError

    @abstractmethod
    def get_latest(
        self,
        athlete_profile_id: UUID,
    ) -> WellnessDay | None:
        """Retourne la dernière journée Wellness disponible."""
        raise NotImplementedError

    @abstractmethod
    def list_range(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
        *,
        provider: str | None = None,
    ) -> list[WellnessDay]:
        """Retourne les journées Wellness d'une période."""
        raise NotImplementedError

    @abstractmethod
    def get_by_date(
        self,
        athlete_profile_id: UUID,
        wellness_date: date,
        *,
        provider: str | None = None,
    ) -> WellnessDay | None:
        """Retourne une journée Wellness précise."""
        raise NotImplementedError