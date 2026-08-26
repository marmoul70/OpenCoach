"""Repository des check-ins quotidiens."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
)


class DailyCheckInRepositoryError(RuntimeError):
    """Erreur d'accès aux check-ins."""


class DailyCheckInRepository(ABC):
    """Interface de persistance des check-ins."""

    @abstractmethod
    def save(
        self,
        athlete_profile_id: UUID,
        checkin: AthleteDailyCheckIn,
    ) -> AthleteDailyCheckIn:
        raise NotImplementedError

    @abstractmethod
    def get_for_date(
        self,
        athlete_profile_id: UUID,
        checkin_date: date,
    ) -> AthleteDailyCheckIn | None:
        raise NotImplementedError
