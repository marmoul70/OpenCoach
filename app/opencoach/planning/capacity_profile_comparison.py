from dataclasses import dataclass
from typing import Literal

from opencoach.models import AthleteProfile

from .athlete_capacity import (
    AthleteCapacityAssessment,
)


ComparisonStatus = Literal[
    "unknown",
    "below_declared",
    "aligned",
    "above_declared",
]


@dataclass(frozen=True)
class CapacityMetricComparison:
    """Comparaison entre une valeur déclarée et une capacité démontrée."""

    declared: float | None
    demonstrated: float

    status: ComparisonStatus
    ratio: float | None


@dataclass(frozen=True)
class CapacityProfileComparison:
    """Compare le profil sportif avec les capacités démontrées."""

    sessions: CapacityMetricComparison
    duration_minutes: CapacityMetricComparison
    distance_km: CapacityMetricComparison

    reasons: tuple[str, ...]

    @property
    def has_mismatch(self) -> bool:
        """Indique si au moins une métrique présente un écart notable."""

        return any(
            metric.status in {
                "below_declared",
                "above_declared",
            }
            for metric in (
                self.sessions,
                self.duration_minutes,
                self.distance_km,
            )
        )


def compare_capacity_to_profile(
    *,
    athlete: AthleteProfile,
    capacity: AthleteCapacityAssessment,
) -> CapacityProfileComparison:
    """Compare les capacités démontrées aux valeurs du profil."""

    training = athlete.training

    sessions = _compare_metric(
        declared=_as_float(
            training.weekly_sessions
        ),
        demonstrated=capacity.weekly_sessions,
    )

    duration_minutes = _compare_metric(
        declared=_as_float(
            training.weekly_duration_minutes
        ),
        demonstrated=(
            capacity.weekly_duration_minutes
        ),
    )

    distance_km = _compare_metric(
        declared=_as_float(
            training.weekly_distance_km
        ),
        demonstrated=(
            capacity.weekly_distance_km
        ),
    )

    reasons: list[str] = []

    _append_reason(
        reasons=reasons,
        label="fréquence hebdomadaire",
        comparison=sessions,
    )

    _append_reason(
        reasons=reasons,
        label="durée hebdomadaire",
        comparison=duration_minutes,
    )

    _append_reason(
        reasons=reasons,
        label="distance hebdomadaire",
        comparison=distance_km,
    )

    return CapacityProfileComparison(
        sessions=sessions,
        duration_minutes=duration_minutes,
        distance_km=distance_km,
        reasons=tuple(reasons),
    )


def _compare_metric(
    *,
    declared: float | None,
    demonstrated: float,
) -> CapacityMetricComparison:
    if declared is None or declared <= 0:
        return CapacityMetricComparison(
            declared=declared,
            demonstrated=demonstrated,
            status="unknown",
            ratio=None,
        )

    ratio = round(
        demonstrated / declared,
        3,
    )

    if ratio < 0.85:
        status: ComparisonStatus = (
            "below_declared"
        )

    elif ratio > 1.15:
        status = "above_declared"

    else:
        status = "aligned"

    return CapacityMetricComparison(
        declared=declared,
        demonstrated=demonstrated,
        status=status,
        ratio=ratio,
    )


def _append_reason(
    *,
    reasons: list[str],
    label: str,
    comparison: CapacityMetricComparison,
) -> None:
    if comparison.status == "below_declared":
        reasons.append(
            f"La {label} démontrée est nettement "
            "inférieure à la valeur déclarée."
        )

    elif comparison.status == "above_declared":
        reasons.append(
            f"La {label} démontrée est supérieure "
            "à la valeur déclarée."
        )

    elif comparison.status == "unknown":
        reasons.append(
            f"La {label} déclarée n'est pas renseignée."
        )


def _as_float(
    value: int | float | None,
) -> float | None:
    if value is None:
        return None

    return float(value)
