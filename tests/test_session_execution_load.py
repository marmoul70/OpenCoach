from datetime import date, datetime

from opencoach.models import Activity, TrainingSession
from opencoach.training import (
    estimate_prescribed_load,
)
from opencoach.training.session_execution import (
    AssessmentStatus,
    assess_session_load,
)


def create_session(
    *,
    session_type: str = "aerobic_easy",
    duration_minutes: int = 60,
    intensity: str = "easy",
) -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(2026, 8, 28),
        type=session_type,
        sport_type="Run",
        title="Séance",
        description="Séance test.",
        duration_minutes=duration_minutes,
        intensity=intensity,
    )


def create_activity(
    *,
    training_load: float | None = 27.0,
    hr_load: float | None = None,
) -> Activity:
    return Activity(
        provider="intervals",
        provider_activity_id="activity-load",
        name="Course",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            28,
            8,
            0,
        ),
        training_load=training_load,
        hr_load=hr_load,
    )


def test_load_uses_existing_prescribed_load_engine() -> None:
    session = create_session()

    expected = estimate_prescribed_load(
        session,
    )

    result = assess_session_load(
        session,
        create_activity(
            training_load=expected,
        ),
    )

    metric = result.training_load

    assert metric is not None
    assert metric.target is not None
    assert metric.target.minimum == expected
    assert metric.target.maximum == expected


def test_exact_training_load_is_compliant() -> None:
    session = create_session()

    planned = estimate_prescribed_load(
        session,
    )

    result = assess_session_load(
        session,
        create_activity(
            training_load=planned,
        ),
    )

    metric = result.training_load

    assert metric is not None
    assert metric.actual_value == planned
    assert metric.delta == 0.0
    assert metric.delta_percent == 0.0

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_training_load_inside_existing_tolerance_is_compliant() -> None:
    session = create_session()

    planned = estimate_prescribed_load(
        session,
    )

    result = assess_session_load(
        session,
        create_activity(
            training_load=(
                planned * 1.15
            ),
        ),
    )

    metric = result.training_load

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_training_load_above_existing_tolerance_is_non_compliant() -> None:
    session = create_session()

    planned = estimate_prescribed_load(
        session,
    )

    result = assess_session_load(
        session,
        create_activity(
            training_load=(
                planned * 1.30
            ),
        ),
    )

    metric = result.training_load

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.NON_COMPLIANT
    )

    assert metric.delta is not None
    assert metric.delta > 0


def test_training_load_below_existing_tolerance_is_non_compliant() -> None:
    session = create_session()

    planned = estimate_prescribed_load(
        session,
    )

    result = assess_session_load(
        session,
        create_activity(
            training_load=(
                planned * 0.70
            ),
        ),
    )

    metric = result.training_load

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.NON_COMPLIANT
    )

    assert metric.delta is not None
    assert metric.delta < 0


def test_missing_activity_is_insufficient_data() -> None:
    result = assess_session_load(
        create_session(),
        None,
    )

    metric = result.training_load

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_missing_training_load_is_insufficient_data() -> None:
    result = assess_session_load(
        create_session(),
        create_activity(
            training_load=None,
        ),
    )

    metric = result.training_load

    assert metric is not None

    assert (
        metric.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_hr_load_is_not_used_as_training_load_fallback() -> None:
    result = assess_session_load(
        create_session(),
        create_activity(
            training_load=None,
            hr_load=50.0,
        ),
    )

    metric = result.training_load

    assert metric is not None
    assert metric.actual_value is None

    assert (
        metric.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_rest_without_activity_is_compliant() -> None:
    session = create_session(
        session_type="rest",
        duration_minutes=1,
        intensity="very_easy",
    )

    result = assess_session_load(
        session,
        None,
    )

    metric = result.training_load

    assert metric is not None
    assert metric.actual_value == 0.0

    assert (
        metric.status
        is AssessmentStatus.COMPLIANT
    )


def test_rest_with_positive_load_is_non_compliant() -> None:
    session = create_session(
        session_type="rest",
        duration_minutes=1,
        intensity="very_easy",
    )

    result = assess_session_load(
        session,
        create_activity(
            training_load=25.0,
        ),
    )

    metric = result.training_load

    assert metric is not None
    assert metric.actual_value == 25.0

    assert (
        metric.status
        is AssessmentStatus.NON_COMPLIANT
    )
