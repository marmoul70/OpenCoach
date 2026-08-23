# scripts/maintenance/inspect-load-reconciliation.py

"""Diagnostic métier de réconciliation de charge OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
    ProgressionAdjustment,
)
from opencoach.planning.weekly.load_reconciliation import (
    reconcile_weekly_load,
)
from opencoach.planning.weekly.load_reconciliation_context import (
    LoadDeviationCause,
    contextualize_weekly_load_reconciliation,
)
from opencoach.planning.weekly.load_reconciliation_policy import (
    build_reconciliation_adjustment,
)


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    planned_load: float
    actual_load: float
    cause: LoadDeviationCause | None = None
    athlete_imposed: bool = False


SCENARIOS = (
    Scenario(
        name="Conforme",
        planned_load=500.0,
        actual_load=490.0,
    ),
    Scenario(
        name="Sous-charge professionnelle",
        planned_load=500.0,
        actual_load=350.0,
        cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        athlete_imposed=True,
    ),
    Scenario(
        name="Sous-charge fatigue",
        planned_load=500.0,
        actual_load=400.0,
        cause=LoadDeviationCause.FATIGUE,
    ),
    Scenario(
        name="Forte sous-charge fatigue",
        planned_load=500.0,
        actual_load=300.0,
        cause=LoadDeviationCause.FATIGUE,
    ),
    Scenario(
        name="Sous-charge maladie",
        planned_load=500.0,
        actual_load=400.0,
        cause=LoadDeviationCause.ILLNESS,
    ),
    Scenario(
        name="Forte sous-charge maladie",
        planned_load=500.0,
        actual_load=300.0,
        cause=LoadDeviationCause.ILLNESS,
    ),
    Scenario(
        name="Sous-charge blessure",
        planned_load=500.0,
        actual_load=400.0,
        cause=LoadDeviationCause.INJURY,
    ),
    Scenario(
        name="Forte sous-charge blessure",
        planned_load=500.0,
        actual_load=300.0,
        cause=LoadDeviationCause.INJURY,
    ),
    Scenario(
        name="Surcharge",
        planned_load=500.0,
        actual_load=600.0,
        cause=LoadDeviationCause.UNKNOWN,
    ),
    Scenario(
        name="Forte surcharge",
        planned_load=500.0,
        actual_load=700.0,
        cause=LoadDeviationCause.UNKNOWN,
    ),
    Scenario(
        name="Choix athlète",
        planned_load=500.0,
        actual_load=350.0,
        cause=LoadDeviationCause.ATHLETE_CHOICE,
        athlete_imposed=True,
    ),
    Scenario(
        name="Données incomplètes",
        planned_load=500.0,
        actual_load=350.0,
        cause=LoadDeviationCause.INCOMPLETE_DATA,
    ),
)


def _percentage(value: float) -> str:
    return f"{value * 100:+.1f}%"


def _load_label(
    adjustment: LoadAdjustment,
) -> str:
    return adjustment.value


def _progression_label(
    adjustment: ProgressionAdjustment,
) -> str:
    return adjustment.value


def main() -> None:
    print()
    print("=" * 132)
    print("OpenCoach — diagnostic réconciliation prévu / réalisé")
    print("=" * 132)
    print()

    print(
        f"{'Scénario':32}"
        f"{'Prévu':>9}"
        f"{'Réalisé':>10}"
        f"{'Écart':>10}"
        f"{'Statut':>24}"
        f"{'Charge suivante':>20}"
        f"{'Progression':>15}"
        f"{'Reprise':>10}"
    )

    print("-" * 132)

    for scenario in SCENARIOS:
        reconciliation = reconcile_weekly_load(
            planned_load=scenario.planned_load,
            actual_load=scenario.actual_load,
        )

        context = contextualize_weekly_load_reconciliation(
            reconciliation=reconciliation,
            cause=scenario.cause,
            athlete_imposed=scenario.athlete_imposed,
        )

        adjustment = build_reconciliation_adjustment(
            context
        )

        print(
            f"{scenario.name:32}"
            f"{scenario.planned_load:9.1f}"
            f"{scenario.actual_load:10.1f}"
            f"{_percentage(reconciliation.relative_delta):>10}"
            f"{reconciliation.status.value:>24}"
            f"{_load_label(adjustment.load):>20}"
            f"{_progression_label(adjustment.progression):>15}"
            f"{str(adjustment.requires_return_to_training):>10}"
        )

    print("-" * 132)
    print()

    print("Interprétation :")
    print()
    print(
        "- Une contrainte professionnelle/personnelle ou un choix "
        "explicite de l'athlète ne doit pas être transformé "
        "automatiquement en fatigue."
    )
    print(
        "- La fatigue ralentit ou met en pause la progression selon "
        "l'importance de l'écart."
    )
    print(
        "- La maladie déclenche une politique plus conservatrice."
    )
    print(
        "- Une forte sous-charge associée à une blessure peut demander "
        "une reconstruction et un retour à l'entraînement."
    )
    print(
        "- Une surcharge protège la semaine suivante au lieu de "
        "poursuivre mécaniquement la progression."
    )
    print()
    print("=" * 132)


if __name__ == "__main__":
    main()
