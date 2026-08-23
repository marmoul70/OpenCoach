"""Allocation dynamique des phases de préparation.

Ce module répartit le temps disponible jusqu'à une course cible entre
les grandes phases de préparation.

Il ne génère aucune séance et aucune semaine détaillée.
Il fournit uniquement le cadre temporel de la trajectoire OpenCoach.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


@dataclass(frozen=True, slots=True)
class PhaseDurationPolicy:
    """Durées minimales et préférées d'une phase."""

    phase: TrainingPhase

    minimum_weeks: int
    preferred_weeks: int

    compressible: bool = True

    def __post_init__(self) -> None:
        if self.minimum_weeks < 0:
            raise ValueError(
                "La durée minimale d'une phase ne peut pas être négative."
            )

        if self.preferred_weeks < self.minimum_weeks:
            raise ValueError(
                "La durée préférée ne peut pas être inférieure "
                "à la durée minimale."
            )


@dataclass(frozen=True, slots=True)
class AllocatedTrainingPhase:
    """Phase effectivement positionnée dans la trajectoire."""

    phase: TrainingPhase

    start_date: date
    end_date: date

    allocated_weeks: int

    compressed: bool

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError(
                "La fin de phase ne peut pas précéder son début."
            )

        if self.allocated_weeks <= 0:
            raise ValueError(
                "Une phase allouée doit durer au moins une semaine."
            )


@dataclass(frozen=True, slots=True)
class CoachingPhaseAllocation:
    """Résultat de l'allocation temporelle des phases."""

    planning_date: date

    target_race_date: date

    phases: tuple[
        AllocatedTrainingPhase,
        ...
    ]

    @property
    def total_weeks(self) -> int:
        return sum(
            phase.allocated_weeks
            for phase in self.phases
        )

    def phase_on(
        self,
        target_date: date,
    ) -> TrainingPhase | None:
        """Retourne la phase couvrant une date donnée."""

        for phase in self.phases:
            if (
                phase.start_date
                <= target_date
                <= phase.end_date
            ):
                return phase.phase

        return None


DEFAULT_PHASE_POLICIES = (
    PhaseDurationPolicy(
        phase=TrainingPhase.BASE,
        minimum_weeks=2,
        preferred_weeks=5,
        compressible=True,
    ),
    PhaseDurationPolicy(
        phase=TrainingPhase.BUILD,
        minimum_weeks=2,
        preferred_weeks=4,
        compressible=True,
    ),
    PhaseDurationPolicy(
        phase=TrainingPhase.SPECIFIC,
        minimum_weeks=2,
        preferred_weeks=4,
        compressible=True,
    ),
    PhaseDurationPolicy(
        phase=TrainingPhase.TAPER,
        minimum_weeks=1,
        preferred_weeks=2,
        compressible=False,
    ),
)


def allocate_coaching_phases(
    *,
    planning_date: date,
    target_race_date: date,
    policies: tuple[
        PhaseDurationPolicy,
        ...
    ] = DEFAULT_PHASE_POLICIES,
) -> CoachingPhaseAllocation:
    """Répartit dynamiquement le temps disponible entre les phases.

    Les semaines disponibles sont distribuées jusqu'à atteindre les
    durées préférées.

    Si le temps disponible est insuffisant, les phases compressibles
    sont réduites jusqu'à leurs minimums.

    Le taper est préservé en priorité lorsqu'il est déclaré
    non compressible.
    """

    if target_race_date <= planning_date:
        raise ValueError(
            "La course cible doit être postérieure "
            "à la date de planification."
        )

    available_days = (
        target_race_date
        - planning_date
    ).days

    available_weeks = max(
        1,
        (available_days + 6) // 7,
    )

    minimum_total = sum(
        policy.minimum_weeks
        for policy in policies
    )

    if available_weeks < minimum_total:
        raise ValueError(
            "Le délai disponible est insuffisant pour respecter "
            "les durées minimales des phases."
        )

    allocated = {
        policy.phase: policy.minimum_weeks
        for policy in policies
    }

    remaining_weeks = (
        available_weeks
        - minimum_total
    )

    while remaining_weeks > 0:
        progressed = False

        for policy in policies:
            current = allocated[
                policy.phase
            ]

            if current >= policy.preferred_weeks:
                continue

            allocated[
                policy.phase
            ] += 1

            remaining_weeks -= 1
            progressed = True

            if remaining_weeks == 0:
                break

        if not progressed:
            break

    if remaining_weeks > 0:
        # Le temps supplémentaire est attribué à la base.
        base_phase = policies[0].phase

        allocated[
            base_phase
        ] += remaining_weeks

    phases: list[
        AllocatedTrainingPhase
    ] = []

    current_start = planning_date

    for policy in policies:
        weeks = allocated[
            policy.phase
        ]

        phase_end = (
            current_start
            + timedelta(
                weeks=weeks,
            )
            - timedelta(
                days=1,
            )
        )

        compressed = (
            weeks
            < policy.preferred_weeks
        )

        phases.append(
            AllocatedTrainingPhase(
                phase=policy.phase,
                start_date=current_start,
                end_date=phase_end,
                allocated_weeks=weeks,
                compressed=compressed,
            )
        )

        current_start = (
            phase_end
            + timedelta(
                days=1,
            )
        )

    return CoachingPhaseAllocation(
        planning_date=planning_date,
        target_race_date=target_race_date,
        phases=tuple(
            phases
        ),
    )
