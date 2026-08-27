from dataclasses import dataclass

from .load_comparison import (
    TrainingLoadComparison,
)


@dataclass(frozen=True)
class RecentTrainingLoad:
    """Synthèse récente des écarts entre charge prévue et charge réelle."""

    days: tuple[
        TrainingLoadComparison,
        ...,
    ]

    analyzed_days: int

    planned_load_total: float
    actual_load_total: float

    above_plan_days: int
    below_plan_days: int
    on_plan_days: int

    broken_rest_days: int
    respected_rest_days: int

    planning_covered_days: int = 0
    unplanned_days: int = 0

    @property
    def planning_coverage_ratio(self) -> float:
        """Part des jours couverts par une prescription OpenCoach."""

        if self.analyzed_days <= 0:
            return 0.0

        return round(
            self.planning_covered_days
            / self.analyzed_days,
            3,
        )

    @property
    def load_delta_total(self) -> float:
        """Écart cumulé entre charge réelle et charge prévue."""
        return round(
            self.actual_load_total
            - self.planned_load_total,
            2,
        )

    @property
    def load_ratio(self) -> float | None:
        """Ratio cumulé entre charge réelle et charge prévue."""

        if self.planned_load_total <= 0:
            return None

        return round(
            self.actual_load_total
            / self.planned_load_total,
            3,
        )

    @property
    def has_training_history(self) -> bool:
        """Indique si au moins un jour contient une charge réelle."""
        return any(
            day.actual_load > 0
            for day in self.days
        )