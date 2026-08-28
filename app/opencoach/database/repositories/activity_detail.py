"""Contrat de persistance des détails d'activité."""

from abc import ABC, abstractmethod
from uuid import UUID

from opencoach.models import ActivityDetail


class ActivityDetailRepository(ABC):
    """Persistance des intervalles et streams d'activité."""

    @abstractmethod
    def save_activity_detail(
        self,
        athlete_profile_id: UUID,
        detail: ActivityDetail,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_activity_detail(
        self,
        athlete_profile_id: UUID,
        activity_id: UUID,
    ) -> ActivityDetail | None:
        raise NotImplementedError
