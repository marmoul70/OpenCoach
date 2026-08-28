from datetime import date, datetime
from uuid import uuid4

import pytest

from opencoach.models import Activity, TrainingSession
from opencoach.training import (
    estimate_prescribed_load,
)
from opencoach.training.session_execution import (
    AssessmentStatus,
    analyze_session_execution,
)


def create_prescription() -> dict:
    return {
        "intensity": {
            "targets": [
                {
                    "reference": "heart_rate",
                    "label": "Fréquence cardiaque",
                    "minimum": 130.0,
                    "maximum": 150.0,
                    "unit": "bpm",
                },
                {
                    "reference": "vma_percent",
                    "label": "Pourcentage VMA",
                    "minimum": 70.0,
                    "maximum": 75.0,
                    "unit": "%",
                    "derived": {
                        "speed_kmh": {
                            "minimum": 10.5,
                            "maximum": 11.25,
                        },
                        "pace_seconds_per_km": {
                            "fastest": 320.0,
                            "slowest": 342.86,
                        },
                    },
                },
            ],
        },
    }


def create_session(
    *,
    session_type: str = "aerobic_easy",
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=date(2026, 8, 28),
        type=session_type,
        sport_type="Run",
        title="Endurance",
        description="Séance test.",
        duration_minutes=60,
        distance_km=10.0,
        elevation_gain_m=200.0,
        intensity=(
            "very_easy"
            if session_type == "rest"
            else "easy"
        ),
        prescription=create_prescription(),
    )


def create_activity(
    *,
    moving_time_seconds: int | None = 3600,
    distance_m: float | None = 10000.0,
    elevation_gain_m: float | None = 200.0,
    average_heart_rate: float | None = 140.0,
    average_speed_mps: float | None = 3.0,
    training_load: float | None = None,
) -> Activity:
    activity = Activity(
        provider="intervals",
        provider_activity_id="execution-test",
        name="Course",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            28,
            8,
            0,
        ),
        moving_time_seconds=moving_time_seconds,
        distance_m=distance_m,
        elevation_gain_m=elevation_gain_m,
        average_heart_rate=average_heart_rate,
        average_speed_mps=average_speed_mps,
        training_load=training_load,
        id=uuid4(),
    )

    return activity


def compliant_activity(
    session: TrainingSession,
) -> Activity:
    return create_activity(
        training_load=(
            estimate_prescribed_load(
                session
            )
        ),
    )


def test_analyzer_requires_persisted_session() -> None:
    session = create_session()
    session.id = None

    with pytest.raises(
        ValueError,
        match="séance persistée",
    ):
        analyze_session_execution(
            session,
            None,
        )


def test_analyzer_groups_all_current_assessments() -> None:
    session = create_session()

    result = analyze_session_execution(
        session,
        compliant_activity(session),
    )

    assert result.session_id == session.id
    assert result.activity_id is not None

    assert result.volume.duration is not None
    assert result.volume.distance is not None
    assert result.volume.elevation_gain is not None

    assert (
        result.intensity.average_heart_rate
        is not None
    )

    assert (
        result.intensity.average_speed
        is not None
    )

    assert (
        result.intensity.average_pace
        is not None
    )

    assert result.load.training_load is not None


def test_fully_compliant_session_is_compliant() -> None:
    session = create_session()

    result = analyze_session_execution(
        session,
        compliant_activity(session),
    )

    assert (
        result.overall_status
        is AssessmentStatus.COMPLIANT
    )


def test_one_non_compliant_metric_makes_session_non_compliant() -> None:
    session = create_session()

    activity = compliant_activity(
        session
    )

    activity.moving_time_seconds = (
        90 * 60
    )

    result = analyze_session_execution(
        session,
        activity,
    )

    assert (
        result.volume.duration.status
        is AssessmentStatus.NON_COMPLIANT
    )

    assert (
        result.overall_status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_partial_metric_makes_session_partial_when_nothing_fails() -> None:
    session = create_session()

    activity = compliant_activity(
        session
    )

    activity.moving_time_seconds = (
        67 * 60
    )

    result = analyze_session_execution(
        session,
        activity,
    )

    assert (
        result.volume.duration.status
        is AssessmentStatus.PARTIAL
    )

    assert (
        result.overall_status
        is AssessmentStatus.PARTIAL
    )


def test_missing_optional_metric_does_not_penalize_session() -> None:
    session = create_session()

    activity = compliant_activity(
        session
    )

    activity.elevation_gain_m = None

    result = analyze_session_execution(
        session,
        activity,
    )

    assert (
        result.volume.elevation_gain.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert (
        result.overall_status
        is AssessmentStatus.COMPLIANT
    )


def test_missing_activity_marks_planned_session_non_compliant() -> None:
    session = create_session()

    result = analyze_session_execution(
        session,
        None,
    )

    assert result.activity_id is None

    assert (
        result.overall_status
        is AssessmentStatus.NON_COMPLIANT
    )

    assert (
        "Aucune activité"
        in result.observations[0]
    )


def test_rest_without_activity_is_compliant() -> None:
    session = create_session(
        session_type="rest",
    )

    result = analyze_session_execution(
        session,
        None,
    )

    assert (
        result.overall_status
        is AssessmentStatus.COMPLIANT
    )

    assert (
        "repos"
        in result.observations[0].lower()
    )


def test_rest_with_positive_training_load_is_non_compliant() -> None:
    session = create_session(
        session_type="rest",
    )

    activity = create_activity(
        training_load=25.0,
    )

    result = analyze_session_execution(
        session,
        activity,
    )

    assert (
        result.load.training_load.status
        is AssessmentStatus.NON_COMPLIANT
    )

    assert (
        result.overall_status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_compliant_result_contains_deterministic_observation() -> None:
    session = create_session()

    result = analyze_session_execution(
        session,
        compliant_activity(session),
    )

    assert (
        "globalement conformes"
        in result.observations[0]
    )
