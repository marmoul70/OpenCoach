from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from opencoach.models import (
    WeeklyTrainingPlan,
)


class WeeklyTrainingPlanRepository(ABC):
    """Persistance des références hebdomadaires."""

    @abstractmethod
    def save_plan(
        self,
        plan: WeeklyTrainingPlan,
    ) -> WeeklyTrainingPlan:
        """Crée ou met à jour le plan d'une semaine."""
        raise NotImplementedError

    @abstractmethod
    def get_plan_for_week(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> WeeklyTrainingPlan | None:
        """Retourne le plan associé à une semaine."""
        raise NotImplementedError
