"""Diagnostic du réancrage multi-semaines OpenCoach."""

from __future__ import annotations

from datetime import date

from opencoach.planning.load_reconciliation_history import (
    analyze_reconciliation_history,
)
from opencoach.planning.multi_week_trajectory_builder import (
    build_multi_week_trajectory,
)
from opencoach.planning.multi_week_trajectory_reanchoring import (
    reanchor_multi_week_trajectory,
)
from opencoach.planning.weekly_load_reconciliation import (
    reconcile_weekly_load,
)
from opencoach.planning.weekly_load_reconciliation_context import (
    LoadDeviationCause,
    contextualize_weekly_load_reconciliation,
)


def build_history():
    weeks = []

    for actual_load in (
        350.0,
        350.0,
        350.0,
    ):
        reconciliation = reconcile_weekly_load(
            planned_load=500.0,
            actual_load=actual_load,
        )

        weeks.append(
            contextualize_weekly_load_reconciliation(
                reconciliation=reconciliation,
                cause=(
                    LoadDeviationCause.PROFESSIONAL_CONSTRAINT
                ),
                athlete_imposed=True,
            )
        )

    return tuple(weeks)


def main() -> None:
    trajectory = build_multi_week_trajectory(
        planning_date=date(
            2027,
            1,
            4,
        ),
        target_race_date=date(
            2027,
            4,
            19,
        ),
        baseline_load=400.0,
    )

    reanchor_date = date(
        2027,
        3,
        22,
    )

    original_week = trajectory.week_on(
        reanchor_date
    )

    if original_week is None:
        raise RuntimeError(
            "Semaine de diagnostic introuvable."
        )

    trend = analyze_reconciliation_history(
        history=build_history(),
        current_reference_load=(
            original_week.progression_reference_before
        ),
    )

    effective = reanchor_multi_week_trajectory(
        trajectory=trajectory,
        from_date=reanchor_date,
        new_reference_load=(
            trend.recommended_reference_load
        ),
        previous_load=350.0,
    )

    print()
    print("=" * 120)
    print(
        "OpenCoach — diagnostic réancrage "
        "de trajectoire"
    )
    print("=" * 120)
    print()

    print(
        f"Statut                  : {trend.status.value}"
    )
    print(
        f"Semaines considérées    : "
        f"{trend.considered_weeks}"
    )
    print(
        f"Sous-charges consécutives: "
        f"{trend.consecutive_under_target_weeks}"
    )
    print(
        f"Écart relatif moyen     : "
        f"{trend.average_relative_delta * 100:+.1f}%"
    )
    print(
        f"Référence avant         : "
        f"{trend.current_reference_load:.1f}"
    )
    print(
        f"Charge observée moyenne : "
        f"{trend.observed_load_reference:.1f}"
    )
    print(
        f"Référence recommandée   : "
        f"{trend.recommended_reference_load:.1f}"
    )
    print()

    print("-" * 120)
    print(
        f"{'Début':12}"
        f"{'Phase':14}"
        f"{'Type':12}"
        f"{'Réf originale':>16}"
        f"{'Réf effective':>16}"
        f"{'Cible originale':>18}"
        f"{'Cible effective':>18}"
    )
    print("-" * 120)

    for original, rebuilt in zip(
        trajectory.weeks,
        effective.weeks,
    ):
        print(
            f"{original.week_start!s:12}"
            f"{original.phase.value:14}"
            f"{original.week_type.value:12}"
            f"{original.progression_reference_before:16.1f}"
            f"{rebuilt.progression_reference_before:16.1f}"
            f"{original.target_load:18.1f}"
            f"{rebuilt.target_load:18.1f}"
        )

    print("-" * 120)
    print()

    past_is_preserved = all(
        original == rebuilt
        for original, rebuilt in zip(
            trajectory.weeks,
            effective.weeks,
        )
        if original.week_end < reanchor_date
    )

    phases_are_preserved = all(
        original.phase is rebuilt.phase
        for original, rebuilt in zip(
            trajectory.weeks,
            effective.weeks,
        )
    )

    week_types_are_preserved = all(
        original.week_type is rebuilt.week_type
        for original, rebuilt in zip(
            trajectory.weeks,
            effective.weeks,
        )
    )

    print(
        f"Passé conservé          : {past_is_preserved}"
    )
    print(
        f"Phases conservées       : {phases_are_preserved}"
    )
    print(
        f"Types semaines conservés: {week_types_are_preserved}"
    )
    print()

    print("=" * 120)


if __name__ == "__main__":
    main()
