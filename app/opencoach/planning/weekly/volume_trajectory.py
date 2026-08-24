"""Trajectoire déterministe du volume hebdomadaire OpenCoach.

Cette brique construit une courbe temporelle multi-semaines à partir :
- d'une baseline de volume assimilé ;
- d'une demande de pic spécifique ;
- d'une succession de phases ;
- de semaines de récupération ;
- d'un taper relatif au pic construit.

Elle ne génère aucune séance concrète.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)
from opencoach.planning.weekly.volume_progression import (
    calculate_weekly_volume_target,
)


@dataclass(frozen=True, slots=True)
class VolumeTrajectoryPhase:
    """Phase utilisée pour construire une trajectoire de volume."""

    phase: TrainingPhase
    weeks: int

    def __post_init__(self) -> None:
        if self.weeks <= 0:
            raise ValueError(
                "Une phase de volume doit durer "
                "au moins une semaine."
            )


@dataclass(frozen=True, slots=True)
class VolumeTrajectoryWeek:
    """État temporel d'une semaine de trajectoire."""

    index: int

    phase: TrainingPhase
    phase_week_index: int

    recovery_week: bool

    progression_reference_before_minutes: float
    progression_reference_after_minutes: float

    target_duration_minutes: float

    def __post_init__(self) -> None:
        if self.index <= 0:
            raise ValueError(
                "L'index de semaine doit être positif."
            )

        if self.phase_week_index <= 0:
            raise ValueError(
                "L'index de semaine de phase "
                "doit être positif."
            )

        values = (
            self.progression_reference_before_minutes,
            self.progression_reference_after_minutes,
            self.target_duration_minutes,
        )

        if any(
            value < 0
            for value in values
        ):
            raise ValueError(
                "Les durées de trajectoire "
                "ne peuvent pas être négatives."
            )


@dataclass(frozen=True, slots=True)
class MultiWeekVolumeTrajectory:
    """Courbe complète de volume multi-semaines."""

    baseline_duration_minutes: float
    goal_demand_minutes: float

    weeks: tuple[
        VolumeTrajectoryWeek,
        ...,
    ]

    def __post_init__(self) -> None:
        if self.baseline_duration_minutes < 0:
            raise ValueError(
                "La baseline de volume "
                "ne peut pas être négative."
            )

        if self.goal_demand_minutes < 0:
            raise ValueError(
                "La demande de volume "
                "ne peut pas être négative."
            )


def build_multi_week_volume_trajectory(
    *,
    baseline_duration_minutes: float,
    goal_demand_minutes: float,
    phases: tuple[
        VolumeTrajectoryPhase,
        ...,
    ],
    maximum_progression_rate: float = 0.10,
    recovery_every_loading_weeks: int | None = None,
    recovery_factor: float = 0.75,
) -> MultiWeekVolumeTrajectory:
    """Construit une trajectoire temporelle multi-semaines."""

    if baseline_duration_minutes < 0:
        raise ValueError(
            "La baseline de volume "
            "ne peut pas être négative."
        )

    if goal_demand_minutes < 0:
        raise ValueError(
            "La demande de volume "
            "ne peut pas être négative."
        )

    if maximum_progression_rate < 0:
        raise ValueError(
            "Le taux maximal de progression "
            "ne peut pas être négatif."
        )

    if (
        recovery_every_loading_weeks
        is not None
        and recovery_every_loading_weeks <= 0
    ):
        raise ValueError(
            "Le cycle de récupération "
            "doit être strictement positif."
        )

    if not 0.0 < recovery_factor <= 1.0:
        raise ValueError(
            "Le facteur de récupération "
            "doit être compris entre 0 et 1."
        )

    weeks: list[
        VolumeTrajectoryWeek
    ] = []

    progression_reference = (
        baseline_duration_minutes
    )

    loading_weeks_since_recovery = 0

    global_week_index = 0

    for trajectory_phase in phases:
        phase = trajectory_phase.phase

        if phase is TrainingPhase.TAPER:
            taper_weeks = _build_taper_weeks(
                start_index=global_week_index + 1,
                progression_reference=(
                    progression_reference
                ),
                weeks=trajectory_phase.weeks,
            )

            weeks.extend(
                taper_weeks
            )

            global_week_index += (
                trajectory_phase.weeks
            )

            continue

        for phase_week_index in range(
            1,
            trajectory_phase.weeks + 1,
        ):
            global_week_index += 1

            progression_reference_before = (
                progression_reference
            )

            next_week_starts_taper = (
                phase_week_index
                == trajectory_phase.weeks
                and _next_phase_is_taper(
                    phases=phases,
                    current_phase=(
                        trajectory_phase
                    ),
                )
            )

            recovery_week = (
                recovery_every_loading_weeks
                is not None
                and loading_weeks_since_recovery
                >= recovery_every_loading_weeks
                and not next_week_starts_taper
            )

            if recovery_week:
                target_duration_minutes = (
                    progression_reference_before
                    * recovery_factor
                )

                progression_reference_after = (
                    progression_reference_before
                )

                loading_weeks_since_recovery = 0

            else:
                target = (
                    calculate_weekly_volume_target(
                        previous_duration_minutes=(
                            progression_reference_before
                        ),
                        phase=phase,
                        maximum_progression_rate=(
                            maximum_progression_rate
                        ),
                        goal_demand_minutes=(
                            goal_demand_minutes
                        ),
                        weeks_remaining=(
                            _remaining_loading_weeks(
                                phases=phases,
                                current_phase=(
                                    trajectory_phase
                                ),
                                current_phase_week_index=(
                                    phase_week_index
                                ),
                            )
                        ),
                    )
                )

                target_duration_minutes = min(
                    target.target_duration_minutes,
                    goal_demand_minutes,
                )

                progression_reference_after = (
                    target_duration_minutes
                )

                progression_reference = (
                    progression_reference_after
                )

                loading_weeks_since_recovery += 1

            weeks.append(
                VolumeTrajectoryWeek(
                    index=global_week_index,
                    phase=phase,
                    phase_week_index=(
                        phase_week_index
                    ),
                    recovery_week=recovery_week,
                    progression_reference_before_minutes=(
                        progression_reference_before
                    ),
                    progression_reference_after_minutes=(
                        progression_reference_after
                    ),
                    target_duration_minutes=(
                        target_duration_minutes
                    ),
                )
            )

    return MultiWeekVolumeTrajectory(
        baseline_duration_minutes=(
            baseline_duration_minutes
        ),
        goal_demand_minutes=(
            goal_demand_minutes
        ),
        weeks=tuple(
            weeks
        ),
    )


def _next_phase_is_taper(
    *,
    phases: tuple[
        VolumeTrajectoryPhase,
        ...,
    ],
    current_phase: VolumeTrajectoryPhase,
) -> bool:
    """Indique si la phase suivante est le taper."""

    for index, phase in enumerate(
        phases
    ):
        if phase is not current_phase:
            continue

        next_index = index + 1

        if next_index >= len(
            phases
        ):
            return False

        return (
            phases[
                next_index
            ].phase
            is TrainingPhase.TAPER
        )

    return False


def _build_taper_weeks(
    *,
    start_index: int,
    progression_reference: float,
    weeks: int,
) -> tuple[
    VolumeTrajectoryWeek,
    ...,
]:
    """Construit un taper relatif au pic de référence."""

    result: list[
        VolumeTrajectoryWeek
    ] = []

    if weeks == 1:
        factors = (
            0.50,
        )
    elif weeks == 2:
        factors = (
            0.75,
            0.50,
        )
    else:
        step = (
            0.50
            / max(
                1,
                weeks - 1,
            )
        )

        factors = tuple(
            max(
                0.50,
                1.0 - step * index,
            )
            for index in range(
                1,
                weeks + 1,
            )
        )

    for phase_week_index, factor in enumerate(
        factors,
        start=1,
    ):
        result.append(
            VolumeTrajectoryWeek(
                index=(
                    start_index
                    + phase_week_index
                    - 1
                ),
                phase=TrainingPhase.TAPER,
                phase_week_index=(
                    phase_week_index
                ),
                recovery_week=False,
                progression_reference_before_minutes=(
                    progression_reference
                ),
                progression_reference_after_minutes=(
                    progression_reference
                ),
                target_duration_minutes=(
                    progression_reference
                    * factor
                ),
            )
        )

    return tuple(
        result
    )


def _remaining_loading_weeks(
    *,
    phases: tuple[
        VolumeTrajectoryPhase,
        ...,
    ],
    current_phase: VolumeTrajectoryPhase,
    current_phase_week_index: int,
) -> int:
    """Compte les semaines de construction restantes hors taper."""

    remaining = (
        current_phase.weeks
        - current_phase_week_index
    )

    current_found = False

    for phase in phases:
        if phase is current_phase:
            current_found = True
            continue

        if not current_found:
            continue

        if phase.phase is TrainingPhase.TAPER:
            continue

        remaining += (
            phase.weeks
        )

    return max(
        0,
        remaining,
    )
