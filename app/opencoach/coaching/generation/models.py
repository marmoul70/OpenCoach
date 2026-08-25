"""Modèles de génération hebdomadaire du coach OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from opencoach.planning.sessions.proposal import (
    SessionProposal,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


@dataclass(frozen=True, slots=True)
class GeneratedTrainingSession:
    """Séance concrète générée pour un créneau hebdomadaire."""

    slot_id: str

    date: date

    day: Weekday

    phase: TrainingPhase

    proposal: SessionProposal

    def __post_init__(
        self,
    ) -> None:
        if not self.slot_id.strip():
            raise ValueError(
                "L'identifiant du créneau ne peut pas être vide."
            )


@dataclass(frozen=True, slots=True)
class GeneratedTrainingWeek:
    """Semaine complète de séances concrètes."""

    week_start: date

    week_end: date

    phase: TrainingPhase

    sessions: tuple[
        GeneratedTrainingSession,
        ...,
    ]

    target_load: float | None = None

    notes: tuple[
        str,
        ...,
    ] = ()

    def __post_init__(
        self,
    ) -> None:
        if self.week_end < self.week_start:
            raise ValueError(
                "La fin de semaine ne peut pas précéder "
                "le début de semaine."
            )

        if (
            self.target_load is not None
            and self.target_load < 0
        ):
            raise ValueError(
                "La charge cible ne peut pas être négative."
            )

        dates = tuple(
            session.date
            for session in self.sessions
        )

        if tuple(sorted(dates)) != dates:
            raise ValueError(
                "Les séances générées doivent être "
                "ordonnées chronologiquement."
            )

        if any(
            session.date < self.week_start
            or session.date > self.week_end
            for session in self.sessions
        ):
            raise ValueError(
                "Une séance générée se trouve hors "
                "de la semaine demandée."
            )

    @property
    def session_count(
        self,
    ) -> int:
        """Nombre de séances générées."""

        return len(
            self.sessions
        )

    @property
    def total_duration_minutes(
        self,
    ) -> int:
        """Volume total planifié pour la semaine."""

        return sum(
            session.proposal.duration_minutes
            for session in self.sessions
        )

    def sessions_for_day(
        self,
        day: Weekday,
    ) -> tuple[
        GeneratedTrainingSession,
        ...,
    ]:
        """Retourne toutes les séances planifiées pour un jour."""

        return tuple(
            session
            for session in self.sessions
            if session.day is day
        )

    def session_for_day(
        self,
        day: Weekday,
    ) -> GeneratedTrainingSession | None:
        """Retourne la première séance du jour si elle existe.

        Cette méthode est conservée pour compatibilité.
        Pour les journées multi-séances, utiliser sessions_for_day().
        """

        sessions = self.sessions_for_day(
            day
        )

        return (
            sessions[0]
            if sessions
            else None
        )
