from dataclasses import dataclass
from typing import Literal

from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
)


CapacityConfidence = Literal[
    "low",
    "medium",
    "high",
]


@dataclass(frozen=True)
class AthleteCapacityAssessment:
    """Estimation prudente des capacités d'entraînement actuelles."""

    weekly_sessions: float
    weekly_duration_minutes: float
    weekly_distance_km: float
    weekly_elevation_gain_m: float
    weekly_training_load: float

    longest_duration_minutes: float | None
    longest_distance_km: float | None
    highest_elevation_gain_m: float | None

    volume_trend: Literal[
        "decreasing",
        "stable",
        "increasing",
    ]

    confidence: CapacityConfidence

    reasons: tuple[str, ...]


def assess_athlete_capacity(
    metrics: TrainingHistoryMetrics,
) -> AthleteCapacityAssessment:
    """Estime les capacités actuelles à partir de l'historique démontré."""

    reasons: list[str] = []

    recent = metrics.last_28_days
    baseline = metrics.last_84_days

    weekly_sessions = _conservative_value(
        recent.sessions,
        baseline.sessions,
    )

    weekly_duration_minutes = _conservative_value(
        recent.duration_minutes,
        baseline.duration_minutes,
    )

    weekly_distance_km = _conservative_value(
        recent.distance_km,
        baseline.distance_km,
    )

    weekly_elevation_gain_m = _conservative_value(
        recent.elevation_gain_m,
        baseline.elevation_gain_m,
    )

    weekly_training_load = _conservative_value(
        recent.training_load,
        baseline.training_load,
    )

    volume_trend = _classify_trend(
        recent.duration_minutes,
        baseline.duration_minutes,
    )

    confidence = _assess_confidence(
        metrics=metrics,
    )

    if volume_trend == "increasing":
        reasons.append(
            "Le volume des 28 derniers jours est supérieur "
            "à la référence des 84 derniers jours."
        )

    elif volume_trend == "decreasing":
        reasons.append(
            "Le volume des 28 derniers jours est inférieur "
            "à la référence des 84 derniers jours."
        )

    else:
        reasons.append(
            "Le volume récent est cohérent avec la tendance "
            "des 84 derniers jours."
        )

    if metrics.longest_duration_minutes is not None:
        reasons.append(
            "Une sortie longue récente est disponible "
            "pour calibrer l'endurance prolongée."
        )

    if confidence == "low":
        reasons.append(
            "L'historique disponible est insuffisant pour "
            "une estimation robuste."
        )

    elif confidence == "medium":
        reasons.append(
            "L'historique permet une estimation partielle "
            "des capacités actuelles."
        )

    else:
        reasons.append(
            "L'historique récent est suffisamment fourni "
            "pour une estimation fiable des capacités actuelles."
        )

    return AthleteCapacityAssessment(
        weekly_sessions=weekly_sessions,
        weekly_duration_minutes=(
            weekly_duration_minutes
        ),
        weekly_distance_km=weekly_distance_km,
        weekly_elevation_gain_m=(
            weekly_elevation_gain_m
        ),
        weekly_training_load=(
            weekly_training_load
        ),
        longest_duration_minutes=(
            metrics.longest_duration_minutes
        ),
        longest_distance_km=(
            metrics.longest_distance_km
        ),
        highest_elevation_gain_m=(
            metrics.highest_elevation_gain_m
        ),
        volume_trend=volume_trend,
        confidence=confidence,
        reasons=tuple(reasons),
    )


def _conservative_value(
    recent: float,
    baseline: float,
) -> float:
    """Retient une capacité démontrée sans extrapolation agressive."""

    if recent <= 0 and baseline <= 0:
        return 0.0

    if baseline <= 0:
        return round(
            recent,
            2,
        )

    if recent <= 0:
        return round(
            baseline,
            2,
        )

    return round(
        min(
            recent,
            baseline * 1.10,
        ),
        2,
    )


def _classify_trend(
    recent: float,
    baseline: float,
) -> Literal[
    "decreasing",
    "stable",
    "increasing",
]:
    if baseline <= 0:
        return "stable"

    ratio = (
        recent
        / baseline
    )

    if ratio < 0.90:
        return "decreasing"

    if ratio > 1.10:
        return "increasing"

    return "stable"


def _assess_confidence(
    *,
    metrics: TrainingHistoryMetrics,
) -> CapacityConfidence:
    sessions_84 = (
        metrics.last_84_days.sessions
        * metrics.last_84_days.weeks
    )

    if sessions_84 < 8:
        return "low"

    if sessions_84 < 24:
        return "medium"

    return "high"
