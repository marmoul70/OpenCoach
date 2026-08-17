from abc import ABC, abstractmethod

from opencoach.models import Activity


class ActivityRepository(ABC):
    """Abstraction de persistance des activités sportives."""

    @abstractmethod
    def save_activity(
        self,
        athlete_profile_id,
        activity: Activity,
    ) -> None:
        """Crée ou met à jour une activité."""
        raise NotImplementedError