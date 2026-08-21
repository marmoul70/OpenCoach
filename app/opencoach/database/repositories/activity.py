from abc import ABC, abstractmethod
from uuid import UUID
from datetime import date

from opencoach.models import Activity


class ActivityRepository(ABC):
    """Abstraction de persistance des activités sportives."""

    @abstractmethod
    def save_activity(
        self,
        athlete_profile_id: UUID,
        activity: Activity,
    ) -> None:
        """Crée ou met à jour une activité."""
        raise NotImplementedError

    @abstractmethod
    def list_activities(
        self,
        athlete_profile_id: UUID,
    ) -> list[Activity]:
        """Retourne les activités d'un athlète."""
        raise NotImplementedError

    @abstractmethod
    def list_activities_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Activity]:
        """Retourne les activités comprises dans une période."""
        raise NotImplementedError

    @abstractmethod
    def get_activity(
        self,
        athlete_profile_id: UUID,
        activity_id: UUID,
    ) -> Activity | None:
        """Retourne une activité par identifiant."""
        raise NotImplementedError