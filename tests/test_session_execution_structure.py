from datetime import date

from opencoach.models import (
    ActivityDetail,
    ActivityInterval,
    TrainingSession,
)
from opencoach.training.session_execution import (
    AssessmentStatus,
    assess_session_structure,
)


def session(
    *,
    repetitions: int = 4,
) -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(2026, 9, 1),
        type="speed_development",
        sport_type="Run",
        title="Vitesse",
        description="Test.",
        duration_minutes=30,
        intensity="hard",
        prescription={
            "work_structure": {
                "type": "repeats",
                "stimulus": "speed_development",
                "intervals": [
                    {
                        "repetitions": repetitions,
                        "work_duration": None,
                        "work_unit": None,
                        "work_distance_meters": 100,
                        "repetition_target": {
                            "distance_meters": 100,
                            "vma_kmh": 15.0,
                            "vma_percent_min": 100,
                            "vma_percent_max": 115,
                            "fast_seconds": 20.0,
                            "slow_seconds": 24.0,
                        },
                        "recovery_duration": 45,
                        "recovery_unit": "seconds",
                    },
                ],
            },
        },
    )


def rep(
    index: int,
    *,
    distance: float = 100.0,
    duration: int = 22,
    recovery: int = 45,
) -> ActivityInterval:
    start = (
        index
        * (
            duration
            + recovery
        )
    )

    return ActivityInterval(
        provider_interval_id=str(index),
        interval_type="WORK",
        label=None,
        start_index=start,
        end_index=start + duration,
        start_time_seconds=start,
        end_time_seconds=start + duration,
        distance_m=distance,
        moving_time_seconds=duration,
        elapsed_time_seconds=duration,
    )


def detail(
    durations=(22, 22, 22, 22),
) -> ActivityDetail:
    intervals = []

    current_start = 0

    for index, duration in enumerate(
        durations
    ):
        intervals.append(
            ActivityInterval(
                provider_interval_id=str(index),
                interval_type="WORK",
                label=None,
                start_index=current_start,
                end_index=(
                    current_start
                    + duration
                ),
                start_time_seconds=current_start,
                end_time_seconds=(
                    current_start
                    + duration
                ),
                distance_m=100.0,
                moving_time_seconds=duration,
                elapsed_time_seconds=duration,
            )
        )

        current_start += (
            duration
            + 45
        )

    return ActivityDetail(
        provider_activity_id="i1",
        intervals=tuple(intervals),
    )


def test_complete_structure_is_compliant() -> None:
    result = assess_session_structure(
        session(),
        detail(),
    )

    assert (
        result.repetition_count.status
        is AssessmentStatus.COMPLIANT
    )

    assert (
        result.work_distance.status
        is AssessmentStatus.COMPLIANT
    )

    assert (
        result.work_duration.status
        is AssessmentStatus.COMPLIANT
    )

    assert (
        result.recovery_duration.status
        is AssessmentStatus.COMPLIANT
    )

    assert (
        result.repetition_regularity.status
        is AssessmentStatus.COMPLIANT
    )

    assert (
        result.repetition_degradation.status
        is AssessmentStatus.COMPLIANT
    )


def test_missing_one_of_five_repetitions_is_partial() -> None:
    result = assess_session_structure(
        session(
            repetitions=5,
        ),
        detail(
            durations=(
                22,
                22,
                22,
                22,
            )
        ),
    )

    assert (
        result.repetition_count.actual_value
        == 4.0
    )

    assert (
        result.repetition_count.status
        is AssessmentStatus.PARTIAL
    )


def test_too_few_repetitions_is_non_compliant() -> None:
    result = assess_session_structure(
        session(
            repetitions=8,
        ),
        detail(
            durations=(
                22,
                22,
                22,
                22,
            )
        ),
    )

    assert (
        result.repetition_count.status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_irregular_repetitions_are_detected() -> None:
    result = assess_session_structure(
        session(),
        detail(
            durations=(
                20,
                21,
                24,
                25,
            )
        ),
    )

    assert (
        result.repetition_regularity.status
        in {
            AssessmentStatus.PARTIAL,
            AssessmentStatus.NON_COMPLIANT,
        }
    )


def test_clear_degradation_is_detected() -> None:
    result = assess_session_structure(
        session(),
        detail(
            durations=(
                20,
                20,
                24,
                24,
            )
        ),
    )

    assert (
        result.repetition_degradation.actual_value
        == 20.0
    )

    assert (
        result.repetition_degradation.status
        is AssessmentStatus.NON_COMPLIANT
    )


def test_non_structured_session_is_not_applicable() -> None:
    normal = TrainingSession(
        id=None,
        date=date(2026, 9, 1),
        type="aerobic_easy",
        sport_type="Run",
        title="Endurance",
        description="Test.",
        duration_minutes=60,
        intensity="easy",
        prescription={
            "version": 1,
        },
    )

    result = assess_session_structure(
        normal,
        detail(),
    )

    assert (
        result.repetition_count.status
        is AssessmentStatus.NOT_APPLICABLE
    )

    assert (
        result.repetition_regularity.status
        is AssessmentStatus.NOT_APPLICABLE
    )


def test_missing_detail_is_insufficient() -> None:
    result = assess_session_structure(
        session(),
        None,
    )

    assert (
        result.repetition_count.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )

    assert (
        result.work_duration.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_recovery_is_computed_between_repetitions() -> None:
    result = assess_session_structure(
        session(),
        detail(),
    )

    assert (
        result.recovery_duration.actual_value
        == 45.0
    )


def test_average_work_duration_uses_detected_repetitions() -> None:
    result = assess_session_structure(
        session(),
        detail(
            durations=(
                21,
                22,
                23,
                24,
            )
        ),
    )

    assert (
        result.work_duration.actual_value
        == 22.5
    )

    assert (
        result.work_duration.status
        is AssessmentStatus.COMPLIANT
    )
