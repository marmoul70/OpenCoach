"""Trajectoire d'entretien OpenCoach sans course principale.

Lorsqu'aucune course principale planifiée n'existe, OpenCoach
maintient les qualités générales de l'athlète sans construire
artificiellement un pic de forme.

La charge oscille autour de la baseline réelle selon un cycle
déterministe :

- semaine modérée ;
- semaine haute ;
- semaine modérée ;
- semaine basse / récupération.

Ce mode ne possède :
- aucune course cible ;
- aucune phase BUILD ;
- aucune phase SPECIFIC ;
- aucun TAPER.

TrainingPhase.BASE reste temporairement utilisée comme phase
physiologique interne afin de réutiliser les prescriptions générales
existantes sans étendre prématurément l'enum TrainingPhase.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
)
from opencoach.planning.trajectory.coaching_phase_allocation import (
    AllocatedTrainingPhase,
)
from opencoach.planning.trajectory.load_recovery_cycle import (
    RecoveryTrigger,
)
from opencoach.planning.trajectory.multi_week import (
    MultiWeekTrajectory,
    TrajectoryWeek,
    TrajectoryWeekType,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


class MaintenanceLoadLevel(StrEnum):
    """Niveau relatif d'une semaine d'entretien."""

    MODERATE = "moderate"
    HIGH = "high"
    LOW = "low"


@dataclass(
    frozen=True,
    slots=True,
)
class MaintenanceCycleStep:
    """Étape élémentaire du cycle d'entretien."""

    level: MaintenanceLoadLevel
    factor: float
    recovery: bool = False

    def __post_init__(self) -> None:
        if self.factor <= 0:
            raise ValueError(
                "Le facteur de charge d'entretien "
                "doit être strictement positif."
            )

        if (
            self.recovery
            and self.level
            is not MaintenanceLoadLevel.LOW
        ):
            raise ValueError(
                "Une récupération planifiée doit utiliser "
                "le niveau LOW."
            )


DEFAULT_MAINTENANCE_CYCLE = (
    MaintenanceCycleStep(
        level=MaintenanceLoadLevel.MODERATE,
        factor=0.95,
    ),
    MaintenanceCycleStep(
        level=MaintenanceLoadLevel.HIGH,
        factor=1.05,
    ),
    MaintenanceCycleStep(
        level=MaintenanceLoadLevel.MODERATE,
        factor=1.00,
    ),
    MaintenanceCycleStep(
        level=MaintenanceLoadLevel.LOW,
        factor=0.80,
        recovery=True,
    ),
)


@dataclass(
    frozen=True,
    slots=True,
)
class GeneralDevelopmentPolicy:
    """Politique temporelle du mode Maintenance.

    Le nom historique de la classe est conservé temporairement
    pour limiter la portée de la migration.
    """

    maintenance_weeks: int = 12

    cycle: tuple[
        MaintenanceCycleStep,
        ...,
    ] = DEFAULT_MAINTENANCE_CYCLE

    def __post_init__(self) -> None:
        if self.maintenance_weeks <= 0:
            raise ValueError(
                "La durée du cycle de maintenance "
                "doit être strictement positive."
            )

        if not self.cycle:
            raise ValueError(
                "Le cycle de maintenance "
                "ne peut pas être vide."
            )

    @property
    def total_weeks(
        self,
    ) -> int:
        return self.maintenance_weeks


@dataclass(
    frozen=True,
    slots=True,
)
class GeneralDevelopmentPhaseAllocation:
    """Allocation temporelle du mode Maintenance."""

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
    """Construit l'horizon temporel du mode Maintenance.

    BASE est conservé temporairement comme phase physiologique
    interne. Il n'existe plus de transition BASE → BUILD.
    """

    end_date = (
        planning_date
        + timedelta(
            weeks=policy.maintenance_weeks,
        )
        - timedelta(days=1)
    )

    phase = AllocatedTrainingPhase(
        phase=TrainingPhase.BASE,
        start_date=planning_date,
        end_date=end_date,
        allocated_weeks=(
            policy.maintenance_weeks
        ),
        compressed=False,
    )

    return GeneralDevelopmentPhaseAllocation(
        planning_date=planning_date,
        phases=(
            phase,
        ),
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
    """Construit une trajectoire d'entretien autour de la baseline."""

    if baseline_load < 0:
        raise ValueError(
            "La charge de référence "
            "ne peut pas être négative."
        )

    if (
        baseline_duration_minutes is not None
        and baseline_duration_minutes < 0
    ):
        raise ValueError(
            "La durée hebdomadaire de référence "
            "ne peut pas être négative."
        )

    allocation = (
        allocate_general_development_phases(
            planning_date=planning_date,
            policy=policy,
        )
    )

    weeks: list[
        TrajectoryWeek
    ] = []

    previous_load = baseline_load

    previous_duration_minutes = (
        baseline_duration_minutes
    )

    for week_index in range(
        1,
        policy.maintenance_weeks + 1,
    ):
        cycle_step = policy.cycle[
            (week_index - 1)
            % len(policy.cycle)
        ]

        week_start = (
            planning_date
            + timedelta(
                weeks=week_index - 1,
            )
        )

        week_end = (
            week_start
            + timedelta(days=6)
        )

        target_load = (
            baseline_load
            * cycle_step.factor
        )

        load_min = (
            target_load
            * 0.95
        )

        load_max = (
            target_load
            * 1.05
        )

        target_duration_minutes = (
            None
            if baseline_duration_minutes is None
            else (
                baseline_duration_minutes
                * cycle_step.factor
            )
        )

        if cycle_step.recovery:
            week_type = (
                TrajectoryWeekType.RECOVERY
            )

            recovery_trigger = (
                RecoveryTrigger.PLANNED
            )

        else:
            week_type = (
                TrajectoryWeekType.LOADING
            )

            recovery_trigger = (
                RecoveryTrigger.NONE
            )

        notes = (
            (
                "Mode maintenance OpenCoach.",
                (
                    "Niveau de charge : "
                    f"{cycle_step.level.value}."
                ),
                (
                    "Charge ancrée sur la baseline "
                    "sans progression cumulative."
                ),
            )
        )

        week = TrajectoryWeek(
            week_start=week_start,
            week_end=week_end,
            phase=TrainingPhase.BASE,
            week_type=week_type,
            previous_load=previous_load,
            progression_reference_before=(
                baseline_load
            ),
            progression_reference_after=(
                baseline_load
            ),
            target_load=target_load,
            load_min=load_min,
            load_max=load_max,
            load_adjustment=(
                LoadAdjustment.MAINTAIN
            ),
            recovery_trigger=(
                recovery_trigger
            ),
            phase_week_index=week_index,
            previous_duration_minutes=(
                previous_duration_minutes
            ),
            progression_reference_duration_before_minutes=(
                baseline_duration_minutes
            ),
            progression_reference_duration_after_minutes=(
                baseline_duration_minutes
            ),
            target_duration_minutes=(
                target_duration_minutes
            ),
            notes=notes,
        )

        weeks.append(
            week
        )

        previous_load = (
            target_load
        )

        if (
            target_duration_minutes
            is not None
        ):
            previous_duration_minutes = (
                target_duration_minutes
            )

    return MultiWeekTrajectory(
        planning_date=planning_date,
        target_race_date=None,
        baseline_load=baseline_load,
        baseline_duration_minutes=(
            baseline_duration_minutes
        ),
        goal_duration_demand_minutes=None,
        weeks=tuple(
            weeks
        ),
    )
