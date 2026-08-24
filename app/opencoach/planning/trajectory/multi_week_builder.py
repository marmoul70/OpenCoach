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
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def build_multi_week_trajectory(
    *,
    planning_date: date,
    target_race_date: date,
    baseline_load: float,
) -> MultiWeekTrajectory:
    """Construit la courbe de progression jusqu'à une course cible."""

    if baseline_load < 0:
        raise ValueError(
            "La charge de référence ne peut pas être négative."
        )

    allocation = allocate_coaching_phases(
        planning_date=planning_date,
        target_race_date=target_race_date,
    )

    weeks: list[TrajectoryWeek] = []

    previous_load = baseline_load
    progression_reference_load = baseline_load

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

            recovery = decide_load_recovery(
                phase=phase,
                loading_weeks_since_recovery=(
                    loading_weeks_since_recovery
                ),
                planned_recovery_allowed=(
                    not next_week_starts_taper
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
            )

            weeks.append(
                week
            )

            previous_load = target_load

    return MultiWeekTrajectory(
        planning_date=planning_date,
        target_race_date=target_race_date,
        baseline_load=baseline_load,
        weeks=tuple(
            weeks
        ),
    )