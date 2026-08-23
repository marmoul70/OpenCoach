"""Créneaux hebdomadaires portant des intentions de séance.

Ce module représente le résultat du placement temporel d'une
SessionIntent.

Il ne contient aucune séance concrète : le coach IA reste responsable
des exercices, intervalles, allures et consignes précises.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.weekly.schedule_types import (
    FatigueBudget,
    Weekday,
)


@dataclass(frozen=True, slots=True)
class WeeklySessionIntentSlot:
    """Créneau hebdomadaire associé à une intention de séance."""

    slot_id: str

    day: Weekday

    intent: SessionIntent

    fatigue_budget: FatigueBudget

    duration_available_minutes: int | None = None

    preserve_next_key_session: bool = False

    preferred_recovery_before_hours: int | None = None
    preferred_recovery_after_hours: int | None = None

    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.slot_id.strip():
            raise ValueError(
                "L'identifiant du créneau ne peut pas être vide."
            )

        if (
            self.duration_available_minutes is not None
            and self.duration_available_minutes <= 0
        ):
            raise ValueError(
                "La durée disponible doit être strictement positive."
            )

        if (
            self.preferred_recovery_before_hours is not None
            and self.preferred_recovery_before_hours < 0
        ):
            raise ValueError(
                "La récupération préférée avant le créneau "
                "ne peut pas être négative."
            )

        if (
            self.preferred_recovery_after_hours is not None
            and self.preferred_recovery_after_hours < 0
        ):
            raise ValueError(
                "La récupération préférée après le créneau "
                "ne peut pas être négative."
            )

        if (
            self.intent.duration_min_minutes is not None
            and self.duration_available_minutes is not None
            and self.intent.duration_min_minutes
            > self.duration_available_minutes
        ):
            raise ValueError(
                "La durée disponible est insuffisante pour "
                "l'intention demandée."
            )

    @property
    def is_key(
        self,
    ) -> bool:
        """Indique si le créneau porte une intention clé."""

        return (
            self.intent.importance
            is SessionIntentImportance.KEY
        )