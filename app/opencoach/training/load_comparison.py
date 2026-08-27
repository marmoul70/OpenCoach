from dataclasses import dataclass
from datetime import date
from typing import Literal


TrainingLoadStatus = Literal[
    "unplanned",
    "rest_respected",
    "rest_broken",
    "below_plan",
    "on_plan",
    "above_plan",
]


@dataclass(frozen=True)
class TrainingLoadComparison:
    """Comparaison entre prescription et entraînement réellement effectué."""

    date: date

    planned_duration_minutes: int
    actual_duration_minutes: int

    planned_load: float
    actual_load: float

    measured_load: float
    estimated_load: float

    planned_sessions_count: int
    actual_sessions_count: int

    status: TrainingLoadStatus

    @property
    def load_delta(self) -> float:
        """Écart de charge entre réalisé et prévu."""
        return round(
            self.actual_load
            - self.planned_load,
            2,
        )

    @property
    def duration_delta_minutes(self) -> int:
        """Écart de durée entre réalisé et prévu."""
        return (
            self.actual_duration_minutes
            - self.planned_duration_minutes
        )

    @property
    def load_ratio(self) -> float | None:
        """Ratio entre charge réalisée et charge prévue."""

        if self.planned_load <= 0:
            return None

        return round(
            self.actual_load
            / self.planned_load,
            3,
        )


def classify_training_load(
    *,
    planned_load: float,
    actual_load: float,
    has_prescription: bool | None = None,
    has_planned_rest: bool | None = None,
    tolerance: float = 0.20,
) -> TrainingLoadStatus:
    """Classe l'écart entre prescription et charge réelle.

    Lorsque le contexte de prescription est fourni, une absence
    de planning OpenCoach est classée ``unplanned`` et un repos
    doit être explicitement prescrit.

    Les appels historiques qui ne fournissent pas encore ce
    contexte conservent temporairement l'ancienne interprétation
    fondée uniquement sur la charge planifiée.
    """

    if has_prescription is None:
        if planned_load <= 0:
            if actual_load <= 0:
                return "rest_respected"

            return "rest_broken"

    elif not has_prescription:
        return "unplanned"

    if has_planned_rest is True:
        if actual_load <= 0:
            return "rest_respected"

        return "rest_broken"

    if planned_load <= 0:
        return "unplanned"

    ratio = (
        actual_load
        / planned_load
    )

    if ratio < 1.0 - tolerance:
        return "below_plan"

    if ratio > 1.0 + tolerance:
        return "above_plan"

    return "on_plan"