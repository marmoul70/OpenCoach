from datetime import date, datetime

from opencoach.models import Activity, TrainingSession
from opencoach.training.session_execution import (
    AssessmentStatus,
    assess_session_intensity,
)


def create_prescription(
    *,
    with_intervals: bool = False,
) -> dict:
    prescription = {
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

    if with_intervals:
        prescription["work_structure"] = {
            "intervals": [
                {
                    "repetitions": 6,
                    "work_distance_meters": 800,
                },
            ],
        }

    return prescription


def create_session(
    *,
    prescription: dict | None = None,
) -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(2026, 8, 28),
        type="aerobic_easy",
        sport_type="Run",
        title="Endurance",
        description="Séance test.",
        duration_minutes=60,
        distance_km=10.0,
        elevation_gain_m=100.0,
        intensity="easy",
        prescription=(
            prescription
            if prescription is not None
            else create_prescription()
        ),
    )


def create_activity(
    *,
    average_heart_rate: float | None = 140.0,
    average_speed_mps: float | None = 3.0,
) -> Activity:
    return Activity(
        provider="intervals",
        provider_activity_id="activity-intensity",
        name="Course",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            28,
            8,
            0,
        ),
        average_heart_rate=average_heart_rate,
        average_speed_mps=average_speed_mps,
    )


def test_average_hr_inside_target_is_compliant() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_heart_rate=140.0,
        ),
    )

    metric = result.average_heart_rate

    assert metric is not None
    assert metric.actual_value == 140.0
    assert metric.delta == 0.0

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_average_hr_slightly_outside_target_is_partial() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_heart_rate=155.0,
        ),
    )

    metric = result.average_heart_rate

    assert metric is not None
    assert metric.delta == 5.0

    assert (
        metric.status
        is AssessmentStatus.PARTIAL
    )


def test_average_hr_far_outside_target_is_non_compliant() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_heart_rate=165.0,
        ),
    )

    metric = result.average_heart_rate

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_missing_hr_data_is_insufficient() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_heart_rate=None,
        ),
    )

    metric = result.average_heart_rate

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_missing_hr_target_is_not_applicable() -> None:
    session = create_session(
        prescription={
            "intensity": {
                "targets": [],
            },
        },
    )

    result = assess_session_intensity(
        session,
        create_activity(),
    )

    metric = result.average_heart_rate

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.NOT_APPLICABLE
    )


def test_average_speed_uses_derived_vma_speed_target() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_speed_mps=3.0,
        ),
    )

    metric = result.average_speed

    assert metric is not None
    assert metric.actual_value == 10.8
    assert metric.target is not None
    assert metric.target.minimum == 10.5
    assert metric.target.maximum == 11.25

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_average_speed_slightly_outside_range_is_partial() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_speed_mps=(
                11.5 / 3.6
            ),
        ),
    )

    metric = result.average_speed

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.PARTIAL
    )


def test_average_speed_far_outside_range_is_non_compliant() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_speed_mps=(
                13.0 / 3.6
            ),
        ),
    )

    metric = result.average_speed

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_average_pace_is_computed_from_average_speed() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_speed_mps=3.0,
        ),
    )

    metric = result.average_pace

    assert metric is not None
    assert metric.actual_value == 333.33
    assert metric.target is not None
    assert metric.target.minimum == 320.0
    assert metric.target.maximum == 342.86

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_missing_speed_data_marks_speed_and_pace_insufficient() -> None:
    result = assess_session_intensity(
        create_session(),
        create_activity(
            average_speed_mps=None,
        ),
    )

    assert result.average_speed is not None
    assert result.average_pace is not None

    assert (
        result.average_speed.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert (
        result.average_pace.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_missing_vma_target_makes_speed_and_pace_not_applicable() -> None:
    session = create_session(
        prescription={
            "intensity": {
                "targets": [
                    {
                        "reference": "heart_rate",
                        "label": "FC",
                        "minimum": 130.0,
                        "maximum": 150.0,
                        "unit": "bpm",
                    },
                ],
            },
        },
    )

    result = assess_session_intensity(
        session,
        create_activity(),
    )

    assert result.average_speed is not None
    assert result.average_pace is not None

    assert (
        result.average_speed.status
        is AssessmentStatus.NOT_APPLICABLE
    )

    assert (
        result.average_pace.status
        is AssessmentStatus.NOT_APPLICABLE
    )


def test_fractionated_session_does_not_use_global_hr_average() -> None:
    session = create_session(
        prescription=create_prescription(
            with_intervals=True,
        ),
    )

    result = assess_session_intensity(
        session,
        create_activity(),
    )

    metric = result.average_heart_rate

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.NOT_APPLICABLE
    )


def test_fractionated_session_does_not_use_global_speed() -> None:
    session = create_session(
        prescription=create_prescription(
            with_intervals=True,
        ),
    )

    result = assess_session_intensity(
        session,
        create_activity(),
    )

    assert result.average_speed is not None
    assert result.average_pace is not None

    assert (
        result.average_speed.status
        is AssessmentStatus.NOT_APPLICABLE
    )

    assert (
        result.average_pace.status
        is AssessmentStatus.NOT_APPLICABLE
    )


def test_missing_activity_with_targets_is_insufficient() -> None:
    result = assess_session_intensity(
        create_session(),
        None,
    )

    assert result.average_heart_rate is not None
    assert result.average_speed is not None
    assert result.average_pace is not None

    assert (
        result.average_heart_rate.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert (
        result.average_speed.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert (
        result.average_pace.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )
