"""Événements susceptibles de modifier une trajectoire d'entraînement.

Les événements décrivent les faits connus par OpenCoach : compétition,
indisponibilité, maladie, blessure ou interruption.

Ils ne déterminent pas directement les séances. Le moteur de trajectoire
interprétera leurs conséquences dans une étape séparée.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TrajectoryEventType(StrEnum):
    """Nature d'un événement affectant la trajectoire."""

    RACE = "race"
    UNAVAILABILITY = "unavailability"
    ILLNESS = "illness"
    INJURY = "injury"
    TRAINING_BREAK = "training_break"


class RacePriority(StrEnum):
    """Importance d'une compétition dans la préparation."""

    A = "A"
    B = "B"
    C = "C"


class EventImpact(StrEnum):
    """Impact estimé de l'événement sur la trajectoire."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class TrajectoryEvent:
    """Événement temporel connu par le moteur de trajectoire."""

    event_id: str
    event_type: TrajectoryEventType

    start_date: date
    end_date: date

    impact: EventImpact

    race_priority: RacePriority | None = None

    athlete_imposed: bool = False

    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError(
                "L'identifiant de l'événement ne peut pas être vide."
            )

        if self.end_date < self.start_date:
            raise ValueError(
                "La fin de l'événement ne peut pas précéder son début."
            )

        if (
            self.event_type is TrajectoryEventType.RACE
            and self.race_priority is None
        ):
            raise ValueError(
                "Une compétition doit définir une priorité A, B ou C."
            )

        if (
            self.event_type is not TrajectoryEventType.RACE
            and self.race_priority is not None
        ):
            raise ValueError(
                "La priorité de course est réservée aux compétitions."
            )
