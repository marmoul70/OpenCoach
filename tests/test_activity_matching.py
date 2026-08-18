from datetime import date, datetime

from opencoach.models import Activity, TrainingSession
from opencoach.training import (
    match_activity_to_session,
)


def create_session() -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(2026, 8, 18),
        type="easy",
        sport_type="Run",
        title="Endurance",
        description="Séance facile.",
        duration_minutes=60,
        distance_km=10.0,
        elevation_gain_m=200.0,
        intensity="Facile",
        heart_rate_zone="Z2",
        status="planned",
    )


def create_activity() -> Activity:
    return Activity(
        provider="intervals",
        provider_activity_id="i-test",
        name="Morning Course à pied",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            18,
            8,
            0,
        ),
        moving_time_seconds=3600,
        distance_m=10000.0,
        elevation_gain_m=200.0,
    )


def test_perfect_activity_match_scores_100() -> None:
    result = match_activity_to_session(
        create_session(),
        create_activity(),
    )

    assert result.score == 100.0
    assert result.sport_matches is True
    assert result.sport_score == 40.0
    assert result.distance_score == 25.0
    assert result.duration_score == 25.0
    assert result.elevation_score == 10.0


def test_activity_match_penalizes_distance_difference() -> None:
    activity = create_activity()
    activity.distance_m = 8000.0

    result = match_activity_to_session(
        create_session(),
        activity,
    )

    assert result.distance_score == 20.0
    assert result.score == 95.0


def test_activity_match_penalizes_duration_difference() -> None:
    activity = create_activity()
    activity.moving_time_seconds = 45 * 60

    result = match_activity_to_session(
        create_session(),
        activity,
    )

    assert result.duration_score == 18.8
    assert result.score == 93.8


def test_activity_match_penalizes_wrong_sport() -> None:
    activity = create_activity()
    activity.sport_type = "Ride"

    result = match_activity_to_session(
        create_session(),
        activity,
    )

    assert result.sport_matches is False
    assert result.sport_score == 0.0
    assert result.score == 60.0


def test_activity_match_accepts_trail_as_run() -> None:
    session = create_session()
    session.sport_type = "Run"

    activity = create_activity()
    activity.sport_type = "TrailRun"

    result = match_activity_to_session(
        session,
        activity,
    )

    assert result.sport_matches is True
    assert result.score == 100.0


def test_activity_match_uses_elapsed_time_as_fallback() -> None:
    activity = create_activity()
    activity.moving_time_seconds = None
    activity.elapsed_time_seconds = 3600

    result = match_activity_to_session(
        create_session(),
        activity,
    )

    assert result.actual_duration_minutes == 60.0
    assert result.duration_score == 25.0


def test_activity_match_normalizes_missing_metrics() -> None:
    session = create_session()

    activity = create_activity()
    activity.distance_m = None
    activity.elevation_gain_m = None
    activity.moving_time_seconds = None
    activity.elapsed_time_seconds = None

    result = match_activity_to_session(
        session,
        activity,
    )

    assert result.distance_score is None
    assert result.duration_score is None
    assert result.elevation_score is None

    # Le seul critère disponible est le sport,
    # donc un sport identique donne 100 % des critères disponibles.
    assert result.score == 100.0


def test_activity_match_score_cannot_be_negative() -> None:
    activity = create_activity()

    activity.distance_m = 50000.0
    activity.moving_time_seconds = 5 * 3600
    activity.elevation_gain_m = 3000.0

    result = match_activity_to_session(
        create_session(),
        activity,
    )

    assert result.distance_score == 0.0
    assert result.duration_score == 0.0
    assert result.elevation_score == 0.0
    assert result.score == 40.0
