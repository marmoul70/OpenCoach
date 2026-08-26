"""Ré-ancrage d'une trajectoire multi-semaines existante.

Ce module recalcule uniquement la partie future d'une trajectoire
à partir d'une nouvelle référence structurelle.

Lorsqu'une charge réellement observée est sensiblement inférieure
à cette référence, une reconnexion progressive est appliquée afin
d'éviter un saut brutal de charge.

Principes :
- le passé n'est jamais réécrit ;
- les phases et types de semaines sont conservés ;
- la référence structurelle reste stable pendant la reconnexion ;
- les semaines de récupération conservent leur rôle de creux ;
- le taper reste prioritaire sur toute reconnexion.
"""

from __future__ import annotations

from datetime import date

from opencoach.planning.trajectory.multi_week import (
    MultiWeekTrajectory,
    TrajectoryMode,
    TrajectoryWeek,
    TrajectoryWeekType,
)
from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
)
from opencoach.planning.trajectory.reconnection import (
    calculate_trajectory_reconnection,
)
from opencoach.planning.weekly.load_progression import (
    WeeklyLoadTarget,
    calculate_weekly_load_target,
)


def reanchor_multi_week_trajectory(
    *,
    trajectory: MultiWeekTrajectory,
    from_date: date,
    new_reference_load: float,
    previous_load: float | None = None,
) -> MultiWeekTrajectory:
    """Ré-ancre le futur d'une trajectoire existante.

    ``new_reference_load`` représente la nouvelle référence
    structurelle.

    ``previous_load`` représente idéalement la dernière charge
    réellement effectuée. Lorsqu'elle est inférieure à la nouvelle
    référence, elle sert de point de départ à une reconnexion
    progressive.

    Si ``previous_load`` n'est pas fourni, la trajectoire est
    recalculée structurellement sans rampe de reconnexion.
    """

    if new_reference_load < 0:
        raise ValueError(
            "La nouvelle charge de référence ne peut pas être négative."
        )

    if (
        previous_load is not None
        and previous_load < 0
    ):
        raise ValueError(
            "La charge précédente ne peut pas être négative."
        )

    if trajectory.mode is TrajectoryMode.MAINTENANCE:
        return _reanchor_maintenance_trajectory(
            trajectory=trajectory,
            from_date=from_date,
            new_reference_load=new_reference_load,
            previous_load=previous_load,
        )

    start_index = _find_week_index(
        trajectory=trajectory,
        target_date=from_date,
    )

    if start_index is None:
        raise ValueError(
            "Aucune semaine de trajectoire ne couvre "
            "la date de réancrage."
        )

    preserved_weeks = list(
        trajectory.weeks[:start_index]
    )

    original_suffix = (
        trajectory.weeks[start_index:]
    )

    progression_reference_load = (
        new_reference_load
    )

    chained_previous_load = (
        previous_load
        if previous_load is not None
        else original_suffix[0].previous_load
    )

    reconnection_active = (
        previous_load is not None
        and previous_load < new_reference_load
    )

    rebuilt_weeks: list[
        TrajectoryWeek
    ] = []

    for original_week in original_suffix:
        progression_reference_before = (
            progression_reference_load
        )

        nominal_target = (
            calculate_weekly_load_target(
                previous_load=(
                    progression_reference_before
                ),
                phase=original_week.phase,
                adjustment=LoadAdjustment.MAINTAIN,
            )
        )

        if (
            original_week.week_type
            is TrajectoryWeekType.TAPER
        ):
            (
                target_load,
                load_min,
                load_max,
                progression_reference_after,
            ) = _build_taper_week(
                nominal_target=nominal_target,
            )

            progression_reference_load = (
                progression_reference_after
            )

            # L'affûtage devient prioritaire :
            # on ne cherche plus à remonter vers la référence.
            reconnection_active = False

        elif (
            original_week.week_type
            is TrajectoryWeekType.RECOVERY
        ):
            (
                target_load,
                load_min,
                load_max,
            ) = _build_recovery_week(
                original_week=original_week,
                nominal_target=nominal_target,
                observed_load=chained_previous_load,
                structural_reference_load=(
                    progression_reference_before
                ),
                reconnection_active=reconnection_active,
            )

            # Une récupération crée uniquement un creux.
            progression_reference_after = (
                progression_reference_before
            )

        elif reconnection_active:
            (
                target_load,
                load_min,
                load_max,
                reconnection_completed,
            ) = _build_reconnection_loading_week(
                nominal_target=nominal_target,
                observed_load=chained_previous_load,
                structural_reference_load=(
                    progression_reference_before
                ),
            )

            # Tant que la reconnexion est active, la référence
            # structurelle reste la destination et ne s'éloigne pas.
            progression_reference_after = (
                progression_reference_before
            )

            if reconnection_completed:
                reconnection_active = False

        else:
            target_load = (
                nominal_target.target_load
            )

            load_min = nominal_target.load_min
            load_max = nominal_target.load_max

            progression_reference_after = (
                nominal_target.target_load
            )

            progression_reference_load = (
                progression_reference_after
            )

        rebuilt_week = TrajectoryWeek(
            week_start=original_week.week_start,
            week_end=original_week.week_end,
            phase=original_week.phase,
            week_type=original_week.week_type,
            previous_load=chained_previous_load,
            progression_reference_before=(
                progression_reference_before
            ),
            progression_reference_after=(
                progression_reference_after
            ),
            target_load=target_load,
            load_min=load_min,
            load_max=load_max,
            load_adjustment=LoadAdjustment.MAINTAIN,
            recovery_trigger=(
                original_week.recovery_trigger
            ),
            phase_week_index=(
                original_week.phase_week_index
            ),
        )

        rebuilt_weeks.append(
            rebuilt_week
        )

        chained_previous_load = (
            target_load
        )

    return MultiWeekTrajectory(
        planning_date=trajectory.planning_date,
        target_race_date=trajectory.target_race_date,
        baseline_load=trajectory.baseline_load,
        mode=trajectory.mode,
        weeks=tuple(
            preserved_weeks
            + rebuilt_weeks
        ),
    )


def _reanchor_maintenance_trajectory(
    *,
    trajectory: MultiWeekTrajectory,
    from_date: date,
    new_reference_load: float,
    previous_load: float | None,
) -> MultiWeekTrajectory:
    """Ré-ancre une Maintenance sans créer de progression cumulative.

    Les rapports relatifs de charge déjà inscrits dans la trajectoire
    sont conservés. Une semaine à 95 %, 105 %, 100 % ou 80 % de
    l'ancienne baseline conserve donc exactement le même rôle autour
    de la nouvelle baseline.
    """

    start_index = _find_week_index(
        trajectory=trajectory,
        target_date=from_date,
    )

    if start_index is None:
        raise ValueError(
            "Aucune semaine de trajectoire ne couvre "
            "la date de réancrage."
        )

    preserved_weeks = list(
        trajectory.weeks[:start_index]
    )

    original_suffix = (
        trajectory.weeks[start_index:]
    )

    rebuilt_weeks: list[
        TrajectoryWeek
    ] = []

    chained_previous_load = (
        previous_load
        if previous_load is not None
        else original_suffix[0].previous_load
    )

    for original_week in original_suffix:
        if trajectory.baseline_load > 0:
            load_factor = (
                original_week.target_load
                / trajectory.baseline_load
            )

            min_factor = (
                original_week.load_min
                / trajectory.baseline_load
            )

            max_factor = (
                original_week.load_max
                / trajectory.baseline_load
            )
        else:
            # Une baseline historique nulle ne permet pas de retrouver
            # mathématiquement le facteur relatif précédent.
            # La nouvelle référence devient alors la cible neutre.
            load_factor = 1.0
            min_factor = 0.95
            max_factor = 1.05

        target_load = (
            new_reference_load
            * load_factor
        )

        load_min = (
            new_reference_load
            * min_factor
        )

        load_max = (
            new_reference_load
            * max_factor
        )

        rebuilt_week = TrajectoryWeek(
            week_start=original_week.week_start,
            week_end=original_week.week_end,
            phase=original_week.phase,
            week_type=original_week.week_type,
            previous_load=chained_previous_load,
            progression_reference_before=(
                new_reference_load
            ),
            progression_reference_after=(
                new_reference_load
            ),
            target_load=target_load,
            load_min=load_min,
            load_max=load_max,
            load_adjustment=(
                original_week.load_adjustment
            ),
            recovery_trigger=(
                original_week.recovery_trigger
            ),
            phase_week_index=(
                original_week.phase_week_index
            ),
            previous_duration_minutes=(
                original_week.previous_duration_minutes
            ),
            progression_reference_duration_before_minutes=(
                original_week
                .progression_reference_duration_before_minutes
            ),
            progression_reference_duration_after_minutes=(
                original_week
                .progression_reference_duration_after_minutes
            ),
            target_duration_minutes=(
                original_week.target_duration_minutes
            ),
            notes=original_week.notes,
        )

        rebuilt_weeks.append(
            rebuilt_week
        )

        chained_previous_load = (
            target_load
        )

    return MultiWeekTrajectory(
        planning_date=trajectory.planning_date,
        target_race_date=trajectory.target_race_date,
        baseline_load=new_reference_load,
        mode=TrajectoryMode.MAINTENANCE,
        baseline_duration_minutes=(
            trajectory.baseline_duration_minutes
        ),
        goal_duration_demand_minutes=(
            trajectory.goal_duration_demand_minutes
        ),
        weeks=tuple(
            preserved_weeks
            + rebuilt_weeks
        ),
    )


def _build_reconnection_loading_week(
    *,
    nominal_target: WeeklyLoadTarget,
    observed_load: float,
    structural_reference_load: float,
) -> tuple[
    float,
    float,
    float,
    bool,
]:
    """Construit une semaine de charge pendant la reconnexion."""

    reconnection = (
        calculate_trajectory_reconnection(
            observed_load=observed_load,
            structural_reference_load=(
                structural_reference_load
            ),
        )
    )

    target_load = (
        reconnection.target_load
    )

    load_min, load_max = (
        _scale_tolerance_range(
            target_load=target_load,
            nominal_target=nominal_target,
        )
    )

    return (
        target_load,
        load_min,
        load_max,
        reconnection.structural_reference_reached,
    )


def _build_recovery_week(
    *,
    original_week: TrajectoryWeek,
    nominal_target: WeeklyLoadTarget,
    observed_load: float,
    structural_reference_load: float,
    reconnection_active: bool,
) -> tuple[
    float,
    float,
    float,
]:
    """Reconstruit une récupération sans casser la reconnexion."""

    recovery_factor = (
        _infer_recovery_factor(
            week=original_week,
        )
    )

    recovery_target = (
        nominal_target.target_load
        * recovery_factor
    )

    if reconnection_active:
        reconnection = (
            calculate_trajectory_reconnection(
                observed_load=observed_load,
                structural_reference_load=(
                    structural_reference_load
                ),
            )
        )

        # Une récupération ne doit jamais demander davantage
        # que ce qu'autoriserait déjà la rampe de reconnexion.
        target_load = min(
            recovery_target,
            reconnection.target_load,
        )

    else:
        target_load = (
            recovery_target
        )

    load_min, load_max = (
        _scale_tolerance_range(
            target_load=target_load,
            nominal_target=nominal_target,
        )
    )

    return (
        target_load,
        load_min,
        load_max,
    )


def _build_taper_week(
    *,
    nominal_target: WeeklyLoadTarget,
) -> tuple[
    float,
    float,
    float,
    float,
]:
    """Construit une semaine de taper.

    Le taper est prioritaire sur la reconnexion : une préparation
    proche de la course ne doit pas augmenter la charge simplement
    pour rejoindre une ancienne référence structurelle.
    """

    target_load = (
        nominal_target.target_load
    )

    return (
        target_load,
        nominal_target.load_min,
        nominal_target.load_max,
        target_load,
    )


def _scale_tolerance_range(
    *,
    target_load: float,
    nominal_target: WeeklyLoadTarget,
) -> tuple[
    float,
    float,
]:
    """Transpose les tolérances de phase autour d'une cible effective."""

    if nominal_target.target_load == 0:
        return (
            target_load,
            target_load,
        )

    lower_ratio = (
        nominal_target.load_min
        / nominal_target.target_load
    )

    upper_ratio = (
        nominal_target.load_max
        / nominal_target.target_load
    )

    return (
        target_load * lower_ratio,
        target_load * upper_ratio,
    )


def _find_week_index(
    *,
    trajectory: MultiWeekTrajectory,
    target_date: date,
) -> int | None:
    """Retourne l'index de la semaine couvrant la date demandée."""

    for index, week in enumerate(
        trajectory.weeks
    ):
        if (
            week.week_start
            <= target_date
            <= week.week_end
        ):
            return index

    return None


def _infer_recovery_factor(
    *,
    week: TrajectoryWeek,
) -> float:
    """Retrouve le facteur de récupération de la trajectoire originale."""

    original_nominal_target = (
        calculate_weekly_load_target(
            previous_load=(
                week.progression_reference_before
            ),
            phase=week.phase,
            adjustment=LoadAdjustment.MAINTAIN,
        )
    )

    if (
        original_nominal_target.target_load
        == 0
    ):
        return 1.0

    return (
        week.target_load
        / original_nominal_target.target_load
    )
