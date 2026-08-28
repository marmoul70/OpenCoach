from datetime import date, datetime

from opencoach.models import (
    Activity,
    ActivityDetail,
    ActivityStream,
    ActivityStreams,
    TrainingSession,
)
from opencoach.training.session_execution import (
    AssessmentStatus,
    assess_session_intensity,
)


def prescription(
    *,
    intervals: bool = False,
) -> dict:
    result = {
        "intensity": {
            "targets": [
                {
                    "reference": "heart_rate",
                    "minimum": 130.0,
                    "maximum": 150.0,
                    "unit": "bpm",
                },
                {
                    "reference": "vma_percent",
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

    if intervals:
        result["work_structure"] = {
            "intervals": [
                {
                    "repetitions": 6,
                    "work_distance_meters": 800,
                },
            ],
        }

    return result


def session(
    *,
    intervals: bool = False,
) -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(2026, 8, 28),
        type="aerobic_easy",
        sport_type="Run",
        title="Séance",
        description="Test.",
        duration_minutes=10,
        distance_km=2.0,
        intensity="easy",
        prescription=prescription(
            intervals=intervals
        ),
    )


def activity() -> Activity:
    return Activity(
        provider="intervals",
        provider_activity_id="i123",
        name="Course",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            28,
            8,
            0,
        ),
        average_heart_rate=140.0,
        average_speed_mps=3.0,
    )


def detail(
    *,
    hr=(140, 140, 140, 160, 160, 160),
    speed=(3.0, 3.0, 3.0, 3.0, 3.0, 3.0),
) -> ActivityDetail:
    return ActivityDetail(
        provider_activity_id="i123",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=(0, 1, 2, 3, 4, 5),
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=hr,
            ),
            velocity_smooth=ActivityStream(
                stream_type="velocity_smooth",
                data=speed,
            ),
        ),
    )


def test_hr_adherence_is_compliant_above_80_percent() -> None:
    result = assess_session_intensity(
        session(),
        activity(),
        detail(
            hr=(140, 140, 140, 140, 160, 140),
        ),
    )

    metric = result.time_in_heart_rate_target

    assert metric is not None
    assert metric.actual_value == 80.0

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_hr_adherence_is_partial_between_60_and_80() -> None:
    result = assess_session_intensity(
        session(),
        activity(),
        detail(
            hr=(140, 140, 140, 160, 160, 140),
        ),
    )

    metric = result.time_in_heart_rate_target

    assert metric is not None
    assert metric.actual_value == 60.0

    assert (
        metric.status
        is AssessmentStatus.PARTIAL
    )


def test_hr_adherence_is_non_compliant_below_60() -> None:
    result = assess_session_intensity(
        session(),
        activity(),
        detail(
            hr=(140, 140, 160, 160, 160, 140),
        ),
    )

    metric = result.time_in_heart_rate_target

    assert metric is not None
    assert metric.actual_value == 40.0

    assert (
        metric.status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_missing_hr_samples_are_not_counted_as_failure() -> None:
    result = assess_session_intensity(
        session(),
        activity(),
        detail(
            hr=(140, None, None, 140, 140, 140),
        ),
    )

    metric = result.time_in_heart_rate_target

    assert metric is not None
    assert metric.actual_value == 100.0

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_speed_adherence_uses_velocity_stream() -> None:
    result = assess_session_intensity(
        session(),
        activity(),
        detail(
            speed=(3.0, 3.0, 3.0, 3.0, 4.0, 3.0),
        ),
    )

    metric = result.time_in_pace_target

    assert metric is not None
    assert metric.actual_value == 80.0

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_missing_detail_is_insufficient_data() -> None:
    result = assess_session_intensity(
        session(),
        activity(),
        None,
    )

    assert (
        result.time_in_heart_rate_target.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert (
        result.time_in_pace_target.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_missing_velocity_stream_is_insufficient() -> None:
    activity_detail = ActivityDetail(
        provider_activity_id="i123",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=(0, 1, 2),
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=(140, 140, 140),
            ),
        ),
    )

    result = assess_session_intensity(
        session(),
        activity(),
        activity_detail,
    )

    assert (
        result.time_in_pace_target.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_fractionated_session_does_not_use_global_adherence() -> None:
    result = assess_session_intensity(
        session(
            intervals=True,
        ),
        activity(),
        detail(),
    )

    assert (
        result.time_in_heart_rate_target.status
        is AssessmentStatus.NOT_APPLICABLE
    )

    assert (
        result.time_in_pace_target.status
        is AssessmentStatus.NOT_APPLICABLE
    )
