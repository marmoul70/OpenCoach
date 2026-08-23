from dataclasses import dataclass

from opencoach.models import AthleteProfile

from opencoach.planning.athlete.capacity import (
    AthleteCapacityAssessment,
)
from opencoach.planning.athlete.capacity_profile_comparison import (
    CapacityProfileComparison,
)


@dataclass(frozen=True)
class AthleteTrainingBaseline:
    """Baseline d'entraînement utilisable par le planificateur."""

    weekly_sessions: float
    weekly_duration_minutes: float
    weekly_distance_km: float

    weekly_elevation_gain_m: float
    weekly_training_load: float

    longest_duration_minutes: float | None
    longest_distance_km: float | None
    highest_elevation_gain_m: float | None

    source_confidence: str

    reasons: tuple[str, ...]


def build_training_baseline(
    *,
    athlete: AthleteProfile,
    capacity: AthleteCapacityAssessment,
    comparison: CapacityProfileComparison,
) -> AthleteTrainingBaseline:
    """Construit une baseline prudente à partir du profil et de l'historique."""

    reasons: list[str] = []

    sessions = _resolve_metric(
        declared=_as_float(
            athlete.training.weekly_sessions
        ),
        demonstrated=capacity.weekly_sessions,
        confidence=capacity.confidence,
    )

    duration = _resolve_metric(
        declared=_as_float(
            athlete.training.weekly_duration_minutes
        ),
        demonstrated=(
            capacity.weekly_duration_minutes
        ),
        confidence=capacity.confidence,
    )

    distance = _resolve_metric(
        declared=_as_float(
            athlete.training.weekly_distance_km
        ),
        demonstrated=capacity.weekly_distance_km,
        confidence=capacity.confidence,
    )

    if capacity.confidence == "high":
        reasons.append(
            "La baseline repose principalement sur "
            "l'historique réellement démontré."
        )

    elif capacity.confidence == "medium":
        reasons.append(
            "La baseline combine l'historique disponible "
            "et les valeurs déclarées du profil."
        )

    else:
        reasons.append(
            "L'historique est limité : les valeurs déclarées "
            "du profil sont utilisées avec prudence."
        )

    if comparison.has_mismatch:
        reasons.append(
            "Un écart existe entre le profil déclaré "
            "et les capacités récemment démontrées."
        )

    return AthleteTrainingBaseline(
        weekly_sessions=sessions,
        weekly_duration_minutes=duration,
        weekly_distance_km=distance,
        weekly_elevation_gain_m=(
            capacity.weekly_elevation_gain_m
        ),
        weekly_training_load=(
            capacity.weekly_training_load
        ),
        longest_duration_minutes=(
            capacity.longest_duration_minutes
        ),
        longest_distance_km=(
            capacity.longest_distance_km
        ),
        highest_elevation_gain_m=(
            capacity.highest_elevation_gain_m
        ),
        source_confidence=capacity.confidence,
        reasons=tuple(reasons),
    )


def _resolve_metric(
    *,
    declared: float | None,
    demonstrated: float,
    confidence: str,
) -> float:
    if confidence == "high":
        if demonstrated > 0:
            return round(
                demonstrated,
                2,
            )

        return round(
            declared or 0.0,
            2,
        )

    if confidence == "medium":
        if demonstrated > 0 and declared is not None:
            return round(
                min(
                    demonstrated,
                    declared,
                ),
                2,
            )

        if demonstrated > 0:
            return round(
                demonstrated,
                2,
            )

        return round(
            declared or 0.0,
            2,
        )

    if demonstrated > 0 and declared is not None:
        return round(
            min(
                demonstrated,
                declared,
            ),
            2,
        )

    if declared is not None:
        return round(
            declared,
            2,
        )

    return round(
        demonstrated,
        2,
    )


def _as_float(
    value: int | float | None,
) -> float | None:
    if value is None:
        return None

    return float(value)
