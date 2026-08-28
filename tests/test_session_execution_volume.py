from datetime import date, datetime

import pytest

from opencoach.models import Activity, TrainingSession
from opencoach.training.session_execution import (
    AssessmentStatus,
    MetricTolerance,
    VolumeAssessmentThresholds,
    assess_session_volume,
)


def create_session(
    *,
    duration_minutes: int = 60,
    distance_km: float | None = 10.0,
    elevation_gain_m: float | None = 200.0,
) -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(2026, 8, 28),
        type="easy",
        sport_type="Run",
        title="Endurance",
        description="Séance test.",
        duration_minutes=duration_minutes,
        distance_km=distance_km,
        elevation_gain_m=elevation_gain_m,
        intensity="easy",
    )


def create_activity(
    *,
    moving_time_seconds: int | None = 3600,
    elapsed_time_seconds: int | None = None,
    distance_m: float | None = 10000.0,
    elevation_gain_m: float | None = 200.0,
) -> Activity:
    return Activity(
        provider="intervals",
        provider_activity_id="activity-test",
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
        elapsed_time_seconds=elapsed_time_seconds,
        distance_m=distance_m,
        elevation_gain_m=elevation_gain_m,
    )


def test_volume_assessment_perfect_execution() -> None:
    result = assess_session_volume(
        create_session(),
        create_activity(),
    )

    assert (
        result.duration.status
        is AssessmentStatus.COMPLIANT
    )

    assert (
        result.distance.status
        is AssessmentStatus.COMPLIANT
    )

    assert (
        result.elevation_gain.status
        is AssessmentStatus.COMPLIANT
    )

    assert result.duration.delta == 0.0
    assert result.distance.delta == 0.0
    assert result.elevation_gain.delta == 0.0


def test_duration_uses_moving_time_first() -> None:
    activity = create_activity(
        moving_time_seconds=3600,
        elapsed_time_seconds=4500,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert result.duration.actual_value == 60.0


def test_duration_uses_elapsed_time_as_fallback() -> None:
    activity = create_activity(
        moving_time_seconds=None,
        elapsed_time_seconds=3600,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert result.duration.actual_value == 60.0


def test_duration_is_compliant_at_exact_boundary() -> None:
    activity = create_activity(
        moving_time_seconds=66 * 60,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert result.duration.delta_percent == 10.0

    assert (
        result.duration.status
        is AssessmentStatus.COMPLIANT
    )


def test_duration_is_partial_after_compliant_boundary() -> None:
    activity = create_activity(
        moving_time_seconds=67 * 60,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert (
        result.duration.status
        is AssessmentStatus.PARTIAL
    )


def test_duration_is_partial_at_exact_partial_boundary() -> None:
    activity = create_activity(
        moving_time_seconds=72 * 60,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert result.duration.delta_percent == 20.0

    assert (
        result.duration.status
        is AssessmentStatus.PARTIAL
    )


def test_duration_is_non_compliant_above_partial_boundary() -> None:
    activity = create_activity(
        moving_time_seconds=73 * 60,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert (
        result.duration.status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_duration_penalizes_under_execution_symmetrically() -> None:
    activity = create_activity(
        moving_time_seconds=45 * 60,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert result.duration.delta == -15.0
    assert result.duration.delta_percent == -25.0

    assert (
        result.duration.status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_distance_is_converted_from_meters_to_kilometers() -> None:
    activity = create_activity(
        distance_m=10500.0,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert result.distance.actual_value == 10.5
    assert result.distance.delta == 0.5
    assert result.distance.delta_percent == 5.0

    assert (
        result.distance.status
        is AssessmentStatus.COMPLIANT
    )


def test_distance_without_prescription_is_not_applicable() -> None:
    result = assess_session_volume(
        create_session(
            distance_km=None,
        ),
        create_activity(),
    )

    assert (
        result.distance.status
        is AssessmentStatus.NOT_APPLICABLE
    )

    assert result.distance.target is None
    assert result.distance.actual_value is None


def test_elevation_has_more_flexible_tolerance() -> None:
    result = assess_session_volume(
        create_session(
            elevation_gain_m=200.0,
        ),
        create_activity(
            elevation_gain_m=230.0,
        ),
    )

    assert result.elevation_gain.delta_percent == 15.0

    assert (
        result.elevation_gain.status
        is AssessmentStatus.COMPLIANT
    )


def test_elevation_becomes_partial_after_15_percent() -> None:
    result = assess_session_volume(
        create_session(
            elevation_gain_m=200.0,
        ),
        create_activity(
            elevation_gain_m=240.0,
        ),
    )

    assert result.elevation_gain.delta_percent == 20.0

    assert (
        result.elevation_gain.status
        is AssessmentStatus.PARTIAL
    )


def test_missing_activity_produces_insufficient_data() -> None:
    result = assess_session_volume(
        create_session(),
        None,
    )

    assert (
        result.duration.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert (
        result.distance.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert (
        result.elevation_gain.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_missing_activity_distance_is_insufficient_data() -> None:
    activity = create_activity(
        distance_m=None,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert (
        result.distance.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert result.distance.actual_value is None


def test_missing_activity_elevation_is_insufficient_data() -> None:
    activity = create_activity(
        elevation_gain_m=None,
    )

    result = assess_session_volume(
        create_session(),
        activity,
    )

    assert (
        result.elevation_gain.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_custom_thresholds_can_be_injected() -> None:
    thresholds = VolumeAssessmentThresholds(
        duration=MetricTolerance(
            compliant_percent=5.0,
            partial_percent=10.0,
        ),
        distance=MetricTolerance(
            compliant_percent=5.0,
            partial_percent=10.0,
        ),
        elevation_gain=MetricTolerance(
            compliant_percent=5.0,
            partial_percent=10.0,
        ),
    )

    result = assess_session_volume(
        create_session(),
        create_activity(
            moving_time_seconds=66 * 60,
        ),
        thresholds=thresholds,
    )

    assert (
        result.duration.status
        is AssessmentStatus.PARTIAL
    )


def test_metric_tolerance_rejects_invalid_configuration() -> None:
    with pytest.raises(
        ValueError,
        match="tolérance partielle",
    ):
        MetricTolerance(
            compliant_percent=20.0,
            partial_percent=10.0,
        )
