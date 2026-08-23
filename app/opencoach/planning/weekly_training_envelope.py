"""Enveloppe hebdomadaire produite par la trajectoire OpenCoach.

L'enveloppe décrit les objectifs et contraintes de la semaine.
Elle ne contient aucune séance détaillée.

L'athlète reste l'autorité finale sur ses disponibilités et
sur la réalisation effective de l'entraînement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from .weekly_stimulus_slot import (
    Weekday,
    WeeklyStimulusSlot,
)


class TrainingPhase(StrEnum):
    """Phase courante de la trajectoire de coaching."""

    FOUNDATION = "foundation"
    BASE = "base"
    BUILD = "build"
    SPECIFIC = "specific"
    TAPER = "taper"
    RECOVERY = "recovery"
    RETURN_TO_TRAINING = "return_to_training"


class SchedulePressure(StrEnum):
    """Niveau de contrainte temporelle de la semaine."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class WeeklyTrainingEnvelope:
    """Cadre transmis au futur coach IA hebdomadaire.

    Python définit :
    - la phase ;
    - la trajectoire de charge ;
    - les stimuli nécessaires ;
    - les disponibilités réelles ;
    - les préférences d'espacement.

    Le coach IA transforme ensuite ce cadre en séances concrètes.

    Les disponibilités de l'athlète sont prioritaires : une semaine
    comprimée sur plusieurs jours consécutifs reste valide lorsque
    c'est la réalité de son agenda.
    """

    week_start: date
    week_end: date

    phase: TrainingPhase

    target_load: float | None
    load_min: float | None
    load_max: float | None

    available_days: tuple[Weekday, ...]

    slots: tuple[WeeklyStimulusSlot, ...]

    schedule_pressure: SchedulePressure

    athlete_schedule_constrained: bool = False

    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
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

        if (
            self.load_min is not None
            and self.load_min < 0
        ):
            raise ValueError(
                "La charge minimale ne peut pas être négative."
            )

        if (
            self.load_max is not None
            and self.load_max < 0
        ):
            raise ValueError(
                "La charge maximale ne peut pas être négative."
            )

        if (
            self.load_min is not None
            and self.load_max is not None
            and self.load_min > self.load_max
        ):
            raise ValueError(
                "La charge minimale ne peut pas dépasser "
                "la charge maximale."
            )

        if (
            self.target_load is not None
            and self.load_min is not None
            and self.target_load < self.load_min
        ):
            raise ValueError(
                "La charge cible doit appartenir à la plage autorisée."
            )

        if (
            self.target_load is not None
            and self.load_max is not None
            and self.target_load > self.load_max
        ):
            raise ValueError(
                "La charge cible doit appartenir à la plage autorisée."
            )

        available = set(
            self.available_days
        )

        unavailable_slots = tuple(
            slot
            for slot in self.slots
            if slot.day not in available
        )

        if unavailable_slots:
            raise ValueError(
                "Un créneau d'entraînement a été placé sur "
                "un jour indisponible pour l'athlète."
            )

    @property
    def session_count(self) -> int:
        return len(
            self.slots
        )

    @property
    def consecutive_training_days(self) -> int:
        """Retourne la plus longue séquence de jours entraînés.

        Cette information est descriptive et ne constitue pas
        une interdiction.
        """

        day_indexes = {
            Weekday.MONDAY: 0,
            Weekday.TUESDAY: 1,
            Weekday.WEDNESDAY: 2,
            Weekday.THURSDAY: 3,
            Weekday.FRIDAY: 4,
            Weekday.SATURDAY: 5,
            Weekday.SUNDAY: 6,
        }

        indexes = sorted(
            {
                day_indexes[slot.day]
                for slot in self.slots
            }
        )

        if not indexes:
            return 0

        longest = 1
        current = 1

        for previous, current_day in zip(
            indexes,
            indexes[1:],
        ):
            if current_day == previous + 1:
                current += 1
                longest = max(
                    longest,
                    current,
                )
            else:
                current = 1

        return longest
