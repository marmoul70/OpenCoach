"""Calcul d'une charge de référence robuste.

La baseline sert de point de départ à la trajectoire multi-semaines.
Elle combine plusieurs fenêtres d'historique afin d'éviter qu'une
semaine atypique ne déforme immédiatement toute la progression.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
)


@dataclass(frozen=True, slots=True)
class TrainingLoadBaseline:
    """Charge de référence utilisée par la trajectoire."""

    baseline_load: float

    short_term_load: float
    medium_term_load: float
    long_term_load: float

    confidence: float

    def __post_init__(self) -> None:
        values = (
            self.baseline_load,
            self.short_term_load,
            self.medium_term_load,
            self.long_term_load,
        )

        if any(value < 0 for value in values):
            raise ValueError(
                "Les valeurs de charge ne peuvent pas être négatives."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "La confiance doit être comprise entre 0 et 1."
            )


def calculate_training_load_baseline(
    metrics: TrainingHistoryMetrics,
) -> TrainingLoadBaseline:
    """Calcule une baseline pondérée à partir de l'historique."""

    load_7 = metrics.last_7_days.training_load
    load_28 = metrics.last_28_days.training_load
    load_42 = metrics.last_42_days.training_load
    load_84 = metrics.last_84_days.training_load

    short_term_load = load_7

    medium_term_load = (
        load_28 * 0.6
        + load_42 * 0.4
    )

    long_term_load = load_84

    baseline_load = (
        short_term_load * 0.20
        + medium_term_load * 0.50
        + long_term_load * 0.30
    )

    confidence = _calculate_confidence(
        load_7=load_7,
        load_28=load_28,
        load_42=load_42,
        load_84=load_84,
    )

    return TrainingLoadBaseline(
        baseline_load=round(
            baseline_load,
            2,
        ),
        short_term_load=round(
            short_term_load,
            2,
        ),
        medium_term_load=round(
            medium_term_load,
            2,
        ),
        long_term_load=round(
            long_term_load,
            2,
        ),
        confidence=round(
            confidence,
            2,
        ),
    )


def _calculate_confidence(
    *,
    load_7: float,
    load_28: float,
    load_42: float,
    load_84: float,
) -> float:
    """Estime la stabilité de la référence historique."""

    loads = (
        load_7,
        load_28,
        load_42,
        load_84,
    )

    if all(load == 0 for load in loads):
        return 0.0

    reference = max(
        load_28,
        load_42,
        load_84,
        1.0,
    )

    spread = (
        max(loads)
        - min(loads)
    )

    relative_spread = min(
        1.0,
        spread / reference,
    )

    return max(
        0.0,
        1.0 - relative_spread,
    )
