from dataclasses import dataclass

from opencoach.models import Activity, TrainingSession


SPORT_WEIGHT = 40.0
DISTANCE_WEIGHT = 25.0
DURATION_WEIGHT = 25.0
ELEVATION_WEIGHT = 10.0
BEST_MATCH_THRESHOLD = 75.0

@dataclass(frozen=True)
class ActivityMatchResult:
    """Résultat du matching entre une séance prévue et une activité."""

    score: float

    sport_score: float
    distance_score: float | None
    duration_score: float | None
    elevation_score: float | None

    sport_matches: bool

    planned_distance_km: float | None
    actual_distance_km: float | None

    planned_duration_minutes: int | None
    actual_duration_minutes: float | None

    planned_elevation_gain_m: float | None
    actual_elevation_gain_m: float | None


def match_activity_to_session(
    session: TrainingSession,
    activity: Activity,
) -> ActivityMatchResult:
    """Calcule la correspondance entre séance prévue et activité réalisée."""

    sport_matches = _sport_matches(
        session.sport_type,
        activity.sport_type,
    )

    sport_score = (
        SPORT_WEIGHT
        if sport_matches
        else 0.0
    )

    actual_distance_km = (
        activity.distance_m / 1000
        if activity.distance_m is not None
        else None
    )

    actual_duration_minutes = _get_activity_duration_minutes(
        activity,
    )

    distance_score = _weighted_similarity(
        planned=session.distance_km,
        actual=actual_distance_km,
        weight=DISTANCE_WEIGHT,
    )

    duration_score = _weighted_similarity(
        planned=(
            float(session.duration_minutes)
            if session.duration_minutes > 0
            else None
        ),
        actual=actual_duration_minutes,
        weight=DURATION_WEIGHT,
    )

    elevation_score = _weighted_similarity(
        planned=session.elevation_gain_m,
        actual=activity.elevation_gain_m,
        weight=ELEVATION_WEIGHT,
    )

    available_scores = [
        (SPORT_WEIGHT, sport_score),
    ]

    if distance_score is not None:
        available_scores.append(
            (DISTANCE_WEIGHT, distance_score)
        )

    if duration_score is not None:
        available_scores.append(
            (DURATION_WEIGHT, duration_score)
        )

    if elevation_score is not None:
        available_scores.append(
            (ELEVATION_WEIGHT, elevation_score)
        )

    available_weight = sum(
        weight
        for weight, _ in available_scores
    )

    earned_score = sum(
        score
        for _, score in available_scores
    )

    normalized_score = (
        earned_score / available_weight * 100
        if available_weight > 0
        else 0.0
    )

    return ActivityMatchResult(
        score=round(normalized_score, 1),
        sport_score=round(
            sport_score,
            1,
        ),
        distance_score=_round_optional(
            distance_score,
        ),
        duration_score=_round_optional(
            duration_score,
        ),
        elevation_score=_round_optional(
            elevation_score,
        ),
        sport_matches=sport_matches,
        planned_distance_km=session.distance_km,
        actual_distance_km=_round_optional(
            actual_distance_km,
        ),
        planned_duration_minutes=(
            session.duration_minutes
            if session.duration_minutes > 0
            else None
        ),
        actual_duration_minutes=_round_optional(
            actual_duration_minutes,
        ),
        planned_elevation_gain_m=(
            session.elevation_gain_m
        ),
        actual_elevation_gain_m=(
            activity.elevation_gain_m
        ),
    )


def _weighted_similarity(
    *,
    planned: float | None,
    actual: float | None,
    weight: float,
) -> float | None:
    """Retourne un score pondéré selon l'écart relatif."""

    if planned is None or actual is None:
        return None

    if planned <= 0:
        return None

    relative_error = abs(
        actual - planned
    ) / planned

    similarity = max(
        0.0,
        1.0 - relative_error,
    )

    return similarity * weight


def _get_activity_duration_minutes(
    activity: Activity,
) -> float | None:
    seconds = (
        activity.moving_time_seconds
        if activity.moving_time_seconds is not None
        else activity.elapsed_time_seconds
    )

    if seconds is None:
        return None

    return seconds / 60


def _sport_matches(
    planned_sport: str,
    actual_sport: str,
) -> bool:
    return _normalize_sport(
        planned_sport,
    ) == _normalize_sport(
        actual_sport,
    )


def _normalize_sport(
    sport: str,
) -> str:
    normalized = sport.strip().lower()

    aliases = {
        "running": "run",
        "trailrun": "run",
        "trail running": "run",
        "trail": "run",
        "virtualride": "ride",
        "virtual ride": "ride",
        "cycling": "ride",
        "bike": "ride",
    }

    return aliases.get(
        normalized,
        normalized,
    )


def _round_optional(
    value: float | None,
) -> float | None:
    if value is None:
        return None

    return round(value, 1)
