#!/usr/bin/env python3
"""Affiche une trajectoire OpenCoach sous forme lisible.

Ce script est un outil de diagnostic développeur.
Il ne modifie aucune donnée et ne génère aucune séance.
"""

from __future__ import annotations

from datetime import date

from opencoach.planning.trajectory.multi_week_builder import (
    build_multi_week_trajectory,
)


PLANNING_DATE = date(
    2027,
    1,
    4,
)

TARGET_RACE_DATE = date(
    2027,
    4,
    19,
)

BASELINE_LOAD = 400.0


def percentage_change(
    previous: float,
    current: float,
) -> float:
    if previous == 0:
        return 0.0

    return (
        (current - previous)
        / previous
        * 100.0
    )


def main() -> None:
    trajectory = build_multi_week_trajectory(
        planning_date=PLANNING_DATE,
        target_race_date=TARGET_RACE_DATE,
        baseline_load=BASELINE_LOAD,
    )

    print()
    print("=" * 125)
    print(
        "OpenCoach — diagnostic trajectoire multi-semaines"
    )
    print("=" * 125)
    print()

    print(
        f"Début             : {trajectory.planning_date}"
    )
    print(
        f"Course cible      : {trajectory.target_race_date}"
    )
    print(
        f"Charge référence  : {trajectory.baseline_load:.1f}"
    )
    print(
        f"Nombre de semaines: {trajectory.week_count}"
    )

    print()
    print("-" * 125)

    print(
        f"{'#':>3} "
        f"{'Début':<10} "
        f"{'Phase':<12} "
        f"{'Type':<12} "
        f"{'Idx':>3} "
        f"{'Avant':>8} "
        f"{'Réf av.':>8} "
        f"{'Réf ap.':>8} "
        f"{'Cible':>8} "
        f"{'Δ réel':>8} "
        f"{'Δ prog':>8} "
        f"{'Trigger':<18}"
    )

    print("-" * 125)

    for index, week in enumerate(
        trajectory.weeks,
        start=1,
    ):
        actual_variation = percentage_change(
            week.previous_load,
            week.target_load,
        )

        reference_variation = percentage_change(
            week.progression_reference_before,
            week.progression_reference_after,
        )

        print(
            f"{index:>3} "
            f"{week.week_start.isoformat():<10} "
            f"{week.phase.value:<12} "
            f"{week.week_type.value:<12} "
            f"{week.phase_week_index:>3} "
            f"{week.previous_load:>8.1f} "
            f"{week.progression_reference_before:>8.1f} "
            f"{week.progression_reference_after:>8.1f} "
            f"{week.target_load:>8.1f} "
            f"{actual_variation:>+7.1f}% "
            f"{reference_variation:>+7.1f}% "
            f"{week.recovery_trigger.value:<18}"
        )

    print("-" * 125)

    if trajectory.weeks:
        peak_week = max(
            trajectory.weeks,
            key=lambda week: week.target_load,
        )

        lowest_week = min(
            trajectory.weeks,
            key=lambda week: week.target_load,
        )

        peak_reference_week = max(
            trajectory.weeks,
            key=lambda week: (
                week.progression_reference_after
            ),
        )

        print()
        print(
            "Pic de charge      : "
            f"{peak_week.target_load:.1f} "
            f"({peak_week.week_start}, "
            f"{peak_week.phase.value})"
        )

        print(
            "Pic de référence   : "
            f"{peak_reference_week.progression_reference_after:.1f} "
            f"({peak_reference_week.week_start}, "
            f"{peak_reference_week.phase.value})"
        )

        print(
            "Charge minimale    : "
            f"{lowest_week.target_load:.1f} "
            f"({lowest_week.week_start}, "
            f"{lowest_week.phase.value})"
        )

        print(
            "Charge finale      : "
            f"{trajectory.weeks[-1].target_load:.1f}"
        )

    print()
    print("=" * 125)


if __name__ == "__main__":
    main()