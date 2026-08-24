"""Construction déterministe d'une trajectoire multi-semaines.

Ce module orchestre les briques de périodisation déjà existantes :
allocation des phases, progression de charge et cycles de récupération.

Il ne génère aucune séance concrète.
"""

from __future__ import annotations

from datetime import date, timedelta

from opencoach.planning.trajectory.coaching_phase_allocation import (
    allocate_coaching_phases,
)
from opencoach.planning.trajectory.load_recovery_cycle import (
    decide_load_recovery,
)
from opencoach.planning.trajectory.multi_week import (
    MultiWeekTrajectory,
    TrajectoryWeek,
    TrajectoryWeekType,
)
from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
)
from opencoach.planning.weekly.load_progression import (
    calculate_weekly_load_target,
)
from opencoach.planning.weekly.volume_progression import (
    calculate_weekly_volume_target,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def build_multi_week_trajectory(
    *,
    planning_date: date,
    target_race_date: date,
    baseline_load: float,
    baseline_duration_minutes: float | None = None,
    goal_duration_demand_minutes: float | None = None,
) -> MultiWeekTrajectory:
    """Construit la courbe de progression jusqu'à une course cible."""

    if baseline_load < 0:
        raise ValueError(
            "La charge de référence ne peut pas être négative."
        )

    if (
        baseline_duration_minutes is not None
        and baseline_duration_minutes < 0
    ):
        raise ValueError(
            "La durée hebdomadaire de référence "
            "ne peut pas être négative."
        )

    if (
        goal_duration_demand_minutes is not None
        and goal_duration_demand_minutes < 0
    ):
        raise ValueError(
            "La demande cible de volume "
            "ne peut pas être négative."
        )

    if (
        goal_duration_demand_minutes is not None
        and baseline_duration_minutes is None
    ):
        raise ValueError(
            "Une baseline de durée est requise "
            "pour planifier une demande de volume."
        )

    allocation = allocate_coaching_phases(
        planning_date=planning_date,
        target_race_date=target_race_date,
    )

    weeks: list[TrajectoryWeek] = []

    previous_load = baseline_load
    progression_reference_load = baseline_load

    previous_duration_minutes = (
        baseline_duration_minutes
    )
    progression_reference_duration_minutes = (
        baseline_duration_minutes
    )

    loading_weeks_since_recovery = 0

    for phase_index, allocated_phase in enumerate(
        allocation.phases
    ):
        phase = allocated_phase.phase

        for phase_week_index in range(
            1,
            allocated_phase.allocated_weeks + 1,
        ):
            week_start = (
                allocated_phase.start_date
                + timedelta(
                    weeks=phase_week_index - 1,
                )
            )

            week_end = (
                week_start
                + timedelta(days=6)
            )

            next_week_starts_taper = (
                phase_week_index
                == allocated_phase.allocated_weeks
                and phase_index + 1
                < len(allocation.phases)
                and allocation.phases[
                    phase_index + 1
                ].phase
                is TrainingPhase.TAPER
            )

            specific_loading_weeks_remaining = (
                allocated_phase.allocated_weeks
                - phase_week_index
                + 1
            )

            preserve_short_specific_phase = (
                phase is TrainingPhase.SPECIFIC
                and specific_loading_weeks_remaining <= 2
            )

            recovery = decide_load_recovery(
                phase=phase,
                loading_weeks_since_recovery=(
                    loading_weeks_since_recovery
                ),
                planned_recovery_allowed=(
                    not next_week_starts_taper
                    and not preserve_short_specific_phase
                ),
            )

            progression_reference_before = (
                progression_reference_load
            )

            load_target = calculate_weekly_load_target(
                previous_load=(
                    progression_reference_before
                ),
                phase=phase,
                adjustment=LoadAdjustment.MAINTAIN,
            )

            if recovery.recovery_week:
                target_load = (
                    load_target.target_load
                    * recovery.load_factor
                )

                load_min = (
                    load_target.load_min
                    * recovery.load_factor
                )

                load_max = (
                    load_target.load_max
                    * recovery.load_factor
                )

                week_type = (
                    TrajectoryWeekType.RECOVERY
                )

                # Une semaine de récupération crée un creux temporaire.
                # Elle n'augmente ni n'abaisse la référence construite.
                progression_reference_after = (
                    progression_reference_before
                )

                loading_weeks_since_recovery = 0

            else:
                target_load = (
                    load_target.target_load
                )

                load_min = (
                    load_target.load_min
                )

                load_max = (
                    load_target.load_max
                )

                progression_reference_after = (
                    load_target.target_load
                )

                progression_reference_load = (
                    progression_reference_after
                )

                if phase is TrainingPhase.TAPER:
                    week_type = (
                        TrajectoryWeekType.TAPER
                    )
                else:
                    week_type = (
                        TrajectoryWeekType.LOADING
                    )

                loading_weeks_since_recovery += 1

            (
                duration_reference_before,
                duration_reference_after,
                target_duration_minutes,
            ) = _resolve_weekly_volume(
                baseline_duration_minutes=(
                    baseline_duration_minutes
                ),
                previous_reference_minutes=(
                    progression_reference_duration_minutes
                ),
                phase=phase,
                phase_week_index=phase_week_index,
                phase_week_count=(
                    allocated_phase.allocated_weeks
                ),
                phase_index=phase_index,
                allocation=allocation,
                recovery_week=(
                    recovery.recovery_week
                ),
                recovery_factor=(
                    recovery.load_factor
                ),
                goal_duration_demand_minutes=(
                    goal_duration_demand_minutes
                ),
            )

            if duration_reference_after is not None:
                progression_reference_duration_minutes = (
                    duration_reference_after
                )

            week = TrajectoryWeek(
                week_start=week_start,
                week_end=week_end,
                phase=phase,
                week_type=week_type,
                previous_load=previous_load,
                progression_reference_before=(
                    progression_reference_before
                ),
                progression_reference_after=(
                    progression_reference_after
                ),
                target_load=target_load,
                load_min=load_min,
                load_max=load_max,
                load_adjustment=(
                    LoadAdjustment.MAINTAIN
                ),
                recovery_trigger=(
                    recovery.trigger
                ),
                phase_week_index=phase_week_index,
                previous_duration_minutes=(
                    previous_duration_minutes
                ),
                progression_reference_duration_before_minutes=(
                    duration_reference_before
                ),
                progression_reference_duration_after_minutes=(
                    duration_reference_after
                ),
                target_duration_minutes=(
                    target_duration_minutes
                ),
            )

            weeks.append(
                week
            )

            previous_load = target_load

            if target_duration_minutes is not None:
                previous_duration_minutes = (
                    target_duration_minutes
                )

    return MultiWeekTrajectory(
        planning_date=planning_date,
        target_race_date=target_race_date,
        baseline_load=baseline_load,
        baseline_duration_minutes=(
            baseline_duration_minutes
        ),
        goal_duration_demand_minutes=(
            goal_duration_demand_minutes
        ),
        weeks=tuple(
            weeks
        ),
    )

def _resolve_weekly_volume(
    *,
    baseline_duration_minutes: float | None,
    previous_reference_minutes: float | None,
    phase: TrainingPhase,
    phase_week_index: int,
    phase_week_count: int,
    phase_index: int,
    allocation,
    recovery_week: bool,
    recovery_factor: float,
    goal_duration_demand_minutes: float | None,
) -> tuple[
    float | None,
    float | None,
    float | None,
]:
    """Calcule le volume de la semaine sur la trajectoire commune."""

    if baseline_duration_minutes is None:
        return (
            None,
            None,
            None,
        )

    assert previous_reference_minutes is not None

    reference_before = (
        previous_reference_minutes
    )

    if phase is TrainingPhase.TAPER:
        factor = _taper_volume_factor(
            phase_week_index=phase_week_index,
            phase_week_count=phase_week_count,
        )

        return (
            reference_before,
            reference_before,
            reference_before * factor,
        )

    if recovery_week:
        return (
            reference_before,
            reference_before,
            reference_before * recovery_factor,
        )

    weeks_remaining = (
        _remaining_loading_weeks(
            allocation=allocation,
            phase_index=phase_index,
            phase_week_index=phase_week_index,
        )
    )

    target = calculate_weekly_volume_target(
        previous_duration_minutes=(
            reference_before
        ),
        phase=phase,
        goal_demand_minutes=(
            goal_duration_demand_minutes
        ),
        weeks_remaining=(
            weeks_remaining
            if goal_duration_demand_minutes
            is not None
            else None
        ),
    )

    target_minutes = (
        target.target_duration_minutes
    )

    if goal_duration_demand_minutes is not None:
        target_minutes = min(
            target_minutes,
            goal_duration_demand_minutes,
        )

    return (
        reference_before,
        target_minutes,
        target_minutes,
    )


def _remaining_loading_weeks(
    *,
    allocation,
    phase_index: int,
    phase_week_index: int,
) -> int:
    """Compte les semaines de construction restantes avant taper."""

    current_phase = allocation.phases[
        phase_index
    ]

    remaining = (
        current_phase.allocated_weeks
        - phase_week_index
    )

    for future_phase in allocation.phases[
        phase_index + 1:
    ]:
        if (
            future_phase.phase
            is TrainingPhase.TAPER
        ):
            continue

        remaining += (
            future_phase.allocated_weeks
        )

    return max(
        0,
        remaining,
    )


def _taper_volume_factor(
    *,
    phase_week_index: int,
    phase_week_count: int,
) -> float:
    """Réduit le volume relativement au pic construit."""

    if phase_week_count == 1:
        return 0.50

    if phase_week_count == 2:
        return (
            0.75
            if phase_week_index == 1
            else 0.50
        )

    step = (
        0.50
        / max(
            1,
            phase_week_count - 1,
        )
    )

    return max(
        0.50,
        1.0
        - step * phase_week_index,
    )
