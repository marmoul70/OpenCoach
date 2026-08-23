"""Modèle métier d'une trajectoire d'entraînement multi-semaines.

Une trajectoire décrit l'évolution prévue du cadre d'entraînement
jusqu'à un objectif.

Elle ne contient aucune séance concrète. Les séances sont produites
ultérieurement par le coach IA à partir des enveloppes hebdomadaires.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from opencoach.planning.trajectory.load_recovery_cycle import (
    RecoveryTrigger,
)
from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


class TrajectoryWeekType(StrEnum):
    """Rôle principal d'une semaine dans la trajectoire."""

    LOADING = "loading"
    RECOVERY = "recovery"
    TAPER = "taper"
    RETURN_TO_TRAINING = "return_to_training"
    SUSPENDED = "suspended"


@dataclass(frozen=True, slots=True)
class TrajectoryWeek:
    """Une semaine planifiée dans la courbe de progression.

    previous_load correspond à la charge réellement prévue
    la semaine précédente.

    progression_reference_before correspond au niveau de progression
    utilisé comme référence avant le calcul de la semaine.

    progression_reference_after correspond au niveau de progression
    obtenu après application de la politique de la phase.

    target_load correspond à la charge réellement demandée pour
    la semaine.
    """

    week_start: date
    week_end: date

    phase: TrainingPhase
    week_type: TrajectoryWeekType

    previous_load: float

    progression_reference_before: float
    progression_reference_after: float

    target_load: float
    load_min: float
    load_max: float

    load_adjustment: LoadAdjustment

    recovery_trigger: RecoveryTrigger = RecoveryTrigger.NONE

    phase_week_index: int = 1

    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.week_end < self.week_start:
            raise ValueError(
                "La fin de semaine ne peut pas précéder "
                "le début de semaine."
            )

        if self.phase_week_index < 1:
            raise ValueError(
                "L'index de semaine dans la phase doit être positif."
            )

        loads = (
            self.previous_load,
            self.progression_reference_before,
            self.progression_reference_after,
            self.target_load,
            self.load_min,
            self.load_max,
        )

        if any(load < 0 for load in loads):
            raise ValueError(
                "Les valeurs de charge ne peuvent pas être négatives."
            )

        if self.load_min > self.load_max:
            raise ValueError(
                "La charge minimale ne peut pas dépasser "
                "la charge maximale."
            )

        if not (
            self.load_min
            <= self.target_load
            <= self.load_max
        ):
            raise ValueError(
                "La charge cible doit appartenir "
                "à la plage autorisée."
            )


@dataclass(frozen=True, slots=True)
class MultiWeekTrajectory:
    """Courbe de progression déterministe d'OpenCoach."""

    planning_date: date

    target_race_date: date | None

    baseline_load: float

    weeks: tuple[
        TrajectoryWeek,
        ...
    ]

    def __post_init__(self) -> None:
        if self.baseline_load < 0:
            raise ValueError(
                "La charge de référence ne peut pas être négative."
            )

        if (
            self.target_race_date is not None
            and self.target_race_date < self.planning_date
        ):
            raise ValueError(
                "La course cible ne peut pas précéder "
                "la date de planification."
            )

        previous_start: date | None = None

        for week in self.weeks:
            if (
                previous_start is not None
                and week.week_start <= previous_start
            ):
                raise ValueError(
                    "Les semaines de la trajectoire doivent être "
                    "ordonnées chronologiquement."
                )

            previous_start = week.week_start

    @property
    def week_count(self) -> int:
        return len(self.weeks)

    def week_on(
        self,
        target_date: date,
    ) -> TrajectoryWeek | None:
        """Retourne la semaine couvrant une date donnée."""

        for week in self.weeks:
            if (
                week.week_start
                <= target_date
                <= week.week_end
            ):
                return week

        return None