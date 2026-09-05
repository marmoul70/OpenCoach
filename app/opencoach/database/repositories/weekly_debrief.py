"""Contrat de persistance du débrief hebdomadaire."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from opencoach.coaching.weekly_debrief import (
    WeeklyDebrief,
    WeeklyDebriefFacts,
)


class WeeklyDebriefRepositoryError(RuntimeError):
    """Erreur d'accès à la persistance hebdomadaire."""


class WeeklyDebriefAlreadyClosedError(
    WeeklyDebriefRepositoryError,
):
    """Tentative d'écrasement d'un bilan déjà clôturé."""


@dataclass(frozen=True, slots=True)
class StoredWeeklyDebrief:
    """Débrief hebdomadaire et métadonnées persistées."""

    id: UUID
    athlete_profile_id: UUID

    facts: WeeklyDebriefFacts
    debrief: WeeklyDebrief

    adaptation_payload: dict | None

    generated_at: datetime
    recalculated_at: datetime | None
    planning_updated_at: datetime | None
    notification_sent_at: datetime | None


class WeeklyDebriefRepository(ABC):
    """Interface de persistance d'un bilan hebdomadaire."""

    @abstractmethod
    def save_closed(
        self,
        athlete_profile_id: UUID,
        facts: WeeklyDebriefFacts,
        debrief: WeeklyDebrief,
        *,
        adaptation_payload: dict | None = None,
        allow_recalculation: bool = False,
    ) -> StoredWeeklyDebrief:
        """Persiste un bilan clôturé."""

        raise NotImplementedError

    @abstractmethod
    def get_for_week(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> StoredWeeklyDebrief | None:
        """Retourne le bilan d'une semaine."""

        raise NotImplementedError

    @abstractmethod
    def mark_planning_updated(
        self,
        athlete_profile_id: UUID,
        week_start: date,
        *,
        timestamp: datetime | None = None,
    ) -> StoredWeeklyDebrief | None:
        """Marque l'application de l'adaptation au planning."""

        raise NotImplementedError

    @abstractmethod
    def mark_notification_sent(
        self,
        athlete_profile_id: UUID,
        week_start: date,
        *,
        timestamp: datetime | None = None,
    ) -> StoredWeeklyDebrief | None:
        """Marque l'envoi de la notification de bilan."""

        raise NotImplementedError
