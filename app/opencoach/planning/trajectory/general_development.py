"""Périodisation du développement général OpenCoach.

Ce mode est utilisé lorsqu'aucune course principale planifiée
n'est disponible.

Il poursuit un objectif de progression athlétique générale sans
introduire artificiellement une phase spécifique course ou un taper.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.planning.trajectory.coaching_phase_allocation import (
    AllocatedTrainingPhase,
)
from opencoach.planning.trajectory.multi_week import (
    MultiWeekTrajectory,
)
from opencoach.planning.trajectory.multi_week_builder import (
    build_trajectory_from_phases,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


@dataclass(
    frozen=True,
    slots=True,
)
class GeneralDevelopmentPolicy:
    """Politique temporelle du développement général."""

    base_weeks: int = 6
    build_weeks: int = 6

    def __post_init__(self) -> None:
        if (
            self.base_weeks <= 0
            or self.build_weeks <= 0
        ):
            raise ValueError(
                "Les durées des phases de développement "
                "doivent être strictement positives."
            )

    @property
    def total_weeks(
        self,
    ) -> int:
        return (
            self.base_weeks
            + self.build_weeks
        )


@dataclass(
    frozen=True,
    slots=True,
)
class GeneralDevelopmentPhaseAllocation:
    """Allocation temporelle d'un cycle de développement général."""

    planning_date: date

    phases: tuple[
        AllocatedTrainingPhase,
        ...,
    ]

    @property
    def total_weeks(
        self,
    ) -> int:
        return sum(
            phase.allocated_weeks
            for phase in self.phases
        )

    @property
    def start_date(
        self,
    ) -> date:
        return self.phases[0].start_date

    @property
    def end_date(
        self,
    ) -> date:
        return self.phases[-1].end_date


def allocate_general_development_phases(
    *,
    planning_date: date,
    policy: GeneralDevelopmentPolicy = (
        GeneralDevelopmentPolicy()
    ),
) -> GeneralDevelopmentPhaseAllocation:
    """Construit un cycle BASE → BUILD sans taper."""

    base_start = planning_date

    base_end = (
        base_start
        + timedelta(
            weeks=policy.base_weeks,
        )
        - timedelta(days=1)
    )

    build_start = (
        base_end
        + timedelta(days=1)
    )

    build_end = (
        build_start
        + timedelta(
            weeks=policy.build_weeks,
        )
        - timedelta(days=1)
    )

    phases = (
        AllocatedTrainingPhase(
            phase=TrainingPhase.BASE,
            start_date=base_start,
            end_date=base_end,
            allocated_weeks=(
                policy.base_weeks
            ),
            compressed=False,
        ),
        AllocatedTrainingPhase(
            phase=TrainingPhase.BUILD,
            start_date=build_start,
            end_date=build_end,
            allocated_weeks=(
                policy.build_weeks
            ),
            compressed=False,
        ),
    )

    return GeneralDevelopmentPhaseAllocation(
        planning_date=planning_date,
        phases=phases,
    )


def build_general_development_trajectory(
    *,
    planning_date: date,
    baseline_load: float,
    baseline_duration_minutes: float | None = None,
    policy: GeneralDevelopmentPolicy = (
        GeneralDevelopmentPolicy()
    ),
) -> MultiWeekTrajectory:
    """Construit une trajectoire progressive sans course cible.

    Le développement général réutilise exactement le même moteur
    de charge, volume et récupération que la préparation de course.

    Il ne possède toutefois :
    - aucune course cible ;
    - aucune demande de volume spécifique à une course ;
    - aucune phase SPECIFIC ;
    - aucun TAPER.
    """

    allocation = (
        allocate_general_development_phases(
            planning_date=planning_date,
            policy=policy,
        )
    )

    return build_trajectory_from_phases(
        planning_date=planning_date,
        target_race_date=None,
        allocation=allocation,
        baseline_load=baseline_load,
        baseline_duration_minutes=(
            baseline_duration_minutes
        ),
        goal_duration_demand_minutes=None,
    )
