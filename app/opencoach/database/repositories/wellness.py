from abc import ABC, abstractmethod
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
