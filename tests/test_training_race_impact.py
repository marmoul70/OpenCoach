from datetime import date
from uuid import uuid4

from opencoach.models import Race
from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
    WeeklyTrainingAverages,
)
from opencoach.planning.trajectory.event import (
    EventImpact,
    RacePriority,
)
from opencoach.planning.trajectory.race_impact import (
    build_training_race_event,
    evaluate_training_race_impact,
    build_training_race_recovery_dates
)


def weekly(
    *,
    distance_km: float,
    elevation_gain_m: float,
) -> WeeklyTrainingAverages:
    return WeeklyTrainingAverages(
        weeks=4.0,
        sessions=4.0,
        duration_minutes=300.0,
        distance_km=distance_km,
        elevation_gain_m=(
            elevation_gain_m
        ),
        training_load=250.0,
    )


def metrics() -> TrainingHistoryMetrics:
    reference = weekly(
        distance_km=50.0,
        elevation_gain_m=1500.0,
    )

    return TrainingHistoryMetrics(
        last_7_days=reference,
        last_28_days=reference,
        last_42_days=reference,
        last_84_days=reference,
        longest_activity=None,
        longest_duration_minutes=None,
        longest_distance_km=None,
        highest_elevation_activity=None,
        highest_elevation_gain_m=None,
        long_endurance_reference_minutes=180.0,
    )


def race(
    *,
    distance_km: float,
    elevation_gain_m: float,
) -> Race:
    return Race(
        id=uuid4(),
        date=date(
            2026,
            9,
            6,
        ),
        name="Course préparation",
        location="Jura",
        race_type="trail",
        priority="training",
        distance_km=distance_km,
        elevation_gain_m=(
            elevation_gain_m
        ),
        status="planned",
    )


def test_long_training_race_is_critical() -> None:
    assessment = (
        evaluate_training_race_impact(
            race=race(
                distance_km=50.0,
                elevation_gain_m=2500.0,
            ),
            history_metrics=metrics(),
        )
    )

    assert (
        assessment.impact
        is EventImpact.CRITICAL
    )

    assert (
        assessment.race_priority
        is RacePriority.B
    )

    assert (
        assessment.preparation_days
        == 6
    )

    assert (
        assessment.recovery_days
        == 6
    )


def test_small_training_race_has_lower_impact() -> None:
    assessment = (
        evaluate_training_race_impact(
            race=race(
                distance_km=10.0,
                elevation_gain_m=100.0,
            ),
            history_metrics=metrics(),
        )
    )

    assert assessment.impact in {
        EventImpact.LOW,
        EventImpact.MODERATE,
    }

    assert (
        assessment.race_priority
        is RacePriority.C
    )


def test_critical_training_race_creates_protection_window(
) -> None:
    training_race = race(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    event = build_training_race_event(
        race=training_race,
        history_metrics=metrics(),
    )

    assert event.start_date == date(
        2026,
        8,
        31,
    )

    assert event.end_date == date(
        2026,
        9,
        12,
    )

    assert (
        event.impact
        is EventImpact.CRITICAL
    )

    assert (
        event.race_priority
        is RacePriority.B
    )

def test_critical_training_race_creates_recovery_window() -> None:
    training_race = race(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    recovery_dates = (
        build_training_race_recovery_dates(
            race=training_race,
            history_metrics=metrics(),
        )
    )

    assert recovery_dates == (
        date(2026, 9, 7),
        date(2026, 9, 8),
        date(2026, 9, 9),
        date(2026, 9, 10),
        date(2026, 9, 11),
        date(2026, 9, 12),
    )