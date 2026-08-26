"""Repository des propositions quotidiennes d'adaptation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)


class DailyAdaptationRepositoryError(RuntimeError):
    """Erreur d'accès aux propositions d'adaptation."""


class DailyAdaptationRepository(ABC):
    """Interface de persistance des propositions."""

    @abstractmethod
    def save(
        self,
        athlete_profile_id: UUID,
        proposal: CoachAdaptationProposal,
    ) -> CoachAdaptationProposal:
        raise NotImplementedError

    @abstractmethod
    def delete_for_checkin(
        self,
        athlete_profile_id: UUID,
        checkin_id: UUID,
    ) -> None:
        """Supprime la proposition associée à un check-in."""
        raise NotImplementedError

    @abstractmethod
    def get_for_checkin(
        self,
        athlete_profile_id: UUID,
        checkin_id: UUID,
    ) -> CoachAdaptationProposal | None:
        raise NotImplementedError
