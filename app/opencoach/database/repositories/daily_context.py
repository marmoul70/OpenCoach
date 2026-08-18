from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from opencoach.models import DailyContext


class DailyContextRepository(ABC):
    """Abstraction de persistance du contexte subjectif quotidien."""

    @abstractmethod
    def save(
        self,
        athlete_profile_id: UUID,
        context: DailyContext,
    ) -> DailyContext:
        """Crée ou met à jour le contexte d'une journée."""
        raise NotImplementedError

    @abstractmethod
    def get_by_date(
        self,
        athlete_profile_id: UUID,
        context_date: date,
    ) -> DailyContext | None:
        """Retourne le contexte subjectif d'une journée."""
        raise NotImplementedError
