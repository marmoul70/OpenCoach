from opencoach.planning import (
    TrainingHistoryMetrics,
    WeeklyTrainingAverages,
    assess_athlete_capacity,
)


def create_averages(
    *,
    weeks: float,
    sessions: float,
    duration_minutes: float,
    distance_km: float,
    elevation_gain_m: float,
    training_load: float,
) -> WeeklyTrainingAverages:
    return WeeklyTrainingAverages(
        weeks=weeks,
        sessions=sessions,
        duration_minutes=duration_minutes,
        distance_km=distance_km,
        elevation_gain_m=elevation_gain_m,
        training_load=training_load,
    )


def create_metrics(
    *,
    sessions_84: float = 4.0,
    duration_28: float = 300.0,
    duration_84: float = 290.0,
    distance_28: float = 46.0,
    distance_84: float = 43.0,
    elevation_28: float = 1400.0,
    elevation_84: float = 1200.0,
    load_28: float = 300.0,
    load_84: float = 280.0,
) -> TrainingHistoryMetrics:
    return TrainingHistoryMetrics(
        last_7_days=create_averages(
            weeks=1.0,
            sessions=4.0,
            duration_minutes=310.0,
            distance_km=47.0,
            elevation_gain_m=1500.0,
            training_load=320.0,
        ),
        last_28_days=create_averages(
            weeks=4.0,
            sessions=4.0,
            duration_minutes=duration_28,
            distance_km=distance_28,
            elevation_gain_m=elevation_28,
            training_load=load_28,
        ),
        last_42_days=create_averages(
            weeks=6.0,
            sessions=4.0,
            duration_minutes=295.0,
            distance_km=44.0,
            elevation_gain_m=1300.0,
            training_load=290.0,
        ),
        last_84_days=create_averages(
            weeks=12.0,
            sessions=sessions_84,
            duration_minutes=duration_84,
            distance_km=distance_84,
            elevation_gain_m=elevation_84,
            training_load=load_84,
        ),
        longest_activity=None,
        longest_duration_minutes=165.0,
        longest_distance_km=24.0,
        highest_elevation_activity=None,
        highest_elevation_gain_m=1600.0,
    )


def test_assessment_uses_conservative_recent_capacity() -> None:
    assessment = assess_athlete_capacity(
        create_metrics()
    )

    assert assessment.weekly_sessions == 4.0

    assert (
        assessment.weekly_duration_minutes
        == 300.0
    )

    assert assessment.weekly_distance_km == 46.0

    assert (
        assessment.weekly_elevation_gain_m
        == 1320.0
    )

    assert (
        assessment.weekly_training_load
        == 300.0
    )


def test_large_recent_increase_is_capped() -> None:
    assessment = assess_athlete_capacity(
        create_metrics(
            duration_28=400.0,
            duration_84=300.0,
            distance_28=60.0,
            distance_84=40.0,
        )
    )

    assert (
        assessment.weekly_duration_minutes
        == 330.0
    )

    assert (
        assessment.weekly_distance_km
        == 44.0
    )


def test_detects_increasing_volume() -> None:
    assessment = assess_athlete_capacity(
        create_metrics(
            duration_28=340.0,
            duration_84=300.0,
        )
    )

    assert assessment.volume_trend == (
        "increasing"
    )


def test_detects_stable_volume() -> None:
    assessment = assess_athlete_capacity(
        create_metrics(
            duration_28=305.0,
            duration_84=300.0,
        )
    )

    assert assessment.volume_trend == (
        "stable"
    )


def test_detects_decreasing_volume() -> None:
    assessment = assess_athlete_capacity(
        create_metrics(
            duration_28=250.0,
            duration_84=300.0,
        )
    )

    assert assessment.volume_trend == (
        "decreasing"
    )


def test_high_confidence_with_long_history() -> None:
    assessment = assess_athlete_capacity(
        create_metrics(
            sessions_84=4.0,
        )
    )

    assert assessment.confidence == "high"


def test_medium_confidence_with_partial_history() -> None:
    assessment = assess_athlete_capacity(
        create_metrics(
            sessions_84=1.5,
        )
    )

    assert assessment.confidence == "medium"


def test_low_confidence_with_sparse_history() -> None:
    assessment = assess_athlete_capacity(
        create_metrics(
            sessions_84=0.5,
        )
    )

    assert assessment.confidence == "low"


def test_preserves_long_run_metrics() -> None:
    assessment = assess_athlete_capacity(
        create_metrics()
    )

    assert (
        assessment.longest_duration_minutes
        == 165.0
    )

    assert (
        assessment.longest_distance_km
        == 24.0
    )

    assert (
        assessment.highest_elevation_gain_m
        == 1600.0
    )
