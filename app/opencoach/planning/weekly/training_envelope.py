"""Enveloppe hebdomadaire produite par la trajectoire OpenCoach.

L'enveloppe décrit les objectifs et contraintes de la semaine.
Elle ne contient aucune séance détaillée.

Le contrat métier repose exclusivement sur les intentions de séance
placées dans ``session_slots``.

L'athlète reste l'autorité finale sur ses disponibilités et
sur la réalisation effective de l'entraînement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from opencoach.planning.weekly.session_intent_slot import (
    WeeklySessionIntentSlot,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
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
    """Cadre transmis au futur moteur de génération des séances.

    Python définit :
    - la phase ;
    - la trajectoire de charge ;
    - les intentions de séance ;
    - les disponibilités réelles ;
    - les préférences d'espacement.

    Le moteur de génération des séances transforme ensuite ce cadre en séances concrètes.

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

    available_days: tuple[
        Weekday,
        ...
    ]

    session_slots: tuple[
        WeeklySessionIntentSlot,
        ...
    ]

    schedule_pressure: SchedulePressure

    phase_week_index: int = 1

    athlete_schedule_constrained: bool = False

    reference_duration_minutes: float | None = None
    target_duration_minutes: float | None = None
    long_endurance_reference_minutes: float | None = None

    notes: tuple[
        str,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if self.phase_week_index < 1:
            raise ValueError(
                "L'indice de semaine dans la phase "
                "doit être supérieur ou égal à 1."
            )

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
                "La charge cible doit appartenir à "
                "la plage autorisée."
            )

        if (
            self.target_load is not None
            and self.load_max is not None
            and self.target_load > self.load_max
        ):
            raise ValueError(
                "La charge cible doit appartenir à "
                "la plage autorisée."
            )

        if (
            self.reference_duration_minutes
            is not None
            and self.reference_duration_minutes <= 0
        ):
            raise ValueError(
                "La durée hebdomadaire de référence "
                "doit être strictement positive."
            )

        if (
            self.target_duration_minutes
            is not None
            and self.target_duration_minutes <= 0
        ):
            raise ValueError(
                "La durée hebdomadaire cible "
                "doit être strictement positive."
            )

        if (
            self.long_endurance_reference_minutes
            is not None
            and self.long_endurance_reference_minutes <= 0
        ):
            raise ValueError(
                "La durée de référence de sortie longue "
                "doit être strictement positive."
            )

        available = set(
            self.available_days
        )

        unavailable_slots = tuple(
            slot
            for slot in self.session_slots
            if slot.day not in available
        )

        if unavailable_slots:
            raise ValueError(
                "Un créneau d'entraînement a été placé sur "
                "un jour indisponible pour l'athlète."
            )

    @property
    def session_count(self) -> int:
        """Nombre d'intentions de séance planifiées."""

        return len(
            self.session_slots
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
                for slot in self.session_slots
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