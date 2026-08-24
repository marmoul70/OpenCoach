from dataclasses import dataclass
from statistics import median

from opencoach.models import Activity
from opencoach.training import TrainingStats

from opencoach.planning.history.training import (
    TrainingHistorySnapshot,
)


_LONG_ENDURANCE_SPORT_TYPES = frozenset(
    {
        "Run",
        "TrailRun",
    }
)


@dataclass(frozen=True)
class WeeklyTrainingAverages:
    """Moyennes hebdomadaires dérivées d'une fenêtre d'entraînement."""

    weeks: float

    sessions: float
    duration_minutes: float
    distance_km: float
    elevation_gain_m: float
    training_load: float


@dataclass(frozen=True)
class TrainingHistoryMetrics:
    """Indicateurs dérivés de l'historique récent d'entraînement."""

    last_7_days: WeeklyTrainingAverages
    last_28_days: WeeklyTrainingAverages
    last_42_days: WeeklyTrainingAverages
    last_84_days: WeeklyTrainingAverages

    longest_activity: Activity | None
    longest_duration_minutes: float | None
    longest_distance_km: float | None

    highest_elevation_activity: Activity | None
    highest_elevation_gain_m: float | None

    long_endurance_reference_minutes: float | None = None


def calculate_training_history_metrics(
    snapshot: TrainingHistorySnapshot,
) -> TrainingHistoryMetrics:
    """Calcule les indicateurs dérivés d'un historique multi-fenêtres."""

    longest_activity = _find_longest_activity(
        snapshot.activities_84_days
    )

    long_endurance_reference_minutes = (
        _calculate_long_endurance_reference_minutes(
            activities=snapshot.activities_84_days,
            race_activity_ids=(
                snapshot.race_activity_ids
            ),
        )
    )

    highest_elevation_activity = (
        _find_highest_elevation_activity(
            snapshot.activities_84_days
        )
    )

    return TrainingHistoryMetrics(
        last_7_days=_weekly_averages(
            snapshot.last_7_days,
            days=7,
        ),
        last_28_days=_weekly_averages(
            snapshot.last_28_days,
            days=28,
        ),
        last_42_days=_weekly_averages(
            snapshot.last_42_days,
            days=42,
        ),
        last_84_days=_weekly_averages(
            snapshot.last_84_days,
            days=84,
        ),
        longest_activity=longest_activity,
        longest_duration_minutes=(
            _activity_duration_minutes(
                longest_activity
            )
        ),
        longest_distance_km=(
            _activity_distance_km(
                longest_activity
            )
        ),
        highest_elevation_activity=(
            highest_elevation_activity
        ),
        highest_elevation_gain_m=(
            highest_elevation_activity.elevation_gain_m
            if highest_elevation_activity is not None
            else None
        ),
        long_endurance_reference_minutes=(
            long_endurance_reference_minutes
        ),
    )


def _weekly_averages(
    stats: TrainingStats,
    *,
    days: int,
) -> WeeklyTrainingAverages:
    weeks = days / 7

    return WeeklyTrainingAverages(
        weeks=weeks,
        sessions=round(
            stats.sessions_count / weeks,
            2,
        ),
        duration_minutes=round(
            stats.total_duration_minutes / weeks,
            2,
        ),
        distance_km=round(
            stats.total_distance_km / weeks,
            2,
        ),
        elevation_gain_m=round(
            stats.total_elevation_gain_m / weeks,
            2,
        ),
        training_load=round(
            stats.total_load / weeks,
            2,
        ),
    )


def _find_longest_activity(
    activities: tuple[Activity, ...],
) -> Activity | None:
    activities_with_duration = tuple(
        activity
        for activity in activities
        if _activity_duration_minutes(
            activity
        )
        is not None
    )

    if not activities_with_duration:
        return None

    return max(
        activities_with_duration,
        key=lambda activity: (
            _activity_duration_minutes(
                activity
            )
            or 0
        ),
    )


def _calculate_long_endurance_reference_minutes(
    *,
    activities: tuple[Activity, ...],
    race_activity_ids,
) -> float | None:
    """Calcule une référence robuste de sortie longue."""

    durations = sorted(
        (
            duration
            for activity in activities
            if (
                activity.sport_type
                in _LONG_ENDURANCE_SPORT_TYPES
                and (
                    activity.id is None
                    or activity.id
                    not in race_activity_ids
                )
            )
            if (
                duration := _activity_duration_minutes(
                    activity
                )
            )
            is not None
        ),
        reverse=True,
    )

    if not durations:
        return None

    if len(durations) < 3:
        return durations[0]

    return round(
        float(
            median(
                durations[:3]
            )
        ),
        2,
    )

def _find_highest_elevation_activity(
    activities: tuple[Activity, ...],
) -> Activity | None:
    activities_with_elevation = tuple(
        activity
        for activity in activities
        if activity.elevation_gain_m is not None
    )

    if not activities_with_elevation:
        return None

    return max(
        activities_with_elevation,
        key=lambda activity: (
            activity.elevation_gain_m
            or 0
        ),
    )


def _activity_duration_minutes(
    activity: Activity | None,
) -> float | None:
    if activity is None:
        return None

    duration_seconds = (
        activity.moving_time_seconds
        if activity.moving_time_seconds is not None
        else activity.elapsed_time_seconds
    )

    if duration_seconds is None:
        return None

    return round(
        duration_seconds / 60,
        2,
    )


def _activity_distance_km(
    activity: Activity | None,
) -> float | None:
    if (
        activity is None
        or activity.distance_m is None
    ):
        return None

    return round(
        activity.distance_m / 1000,
        2,
    )
