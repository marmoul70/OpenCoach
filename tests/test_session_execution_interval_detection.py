from opencoach.models import (
    ActivityDetail,
    ActivityInterval,
)
from opencoach.training.session_execution import (
    IntervalSetPrescription,
    RepetitionTarget,
    detect_repetitions,
)


def interval(
    *,
    start: int,
    end: int,
    distance: float,
    duration: int,
    speed: float | None = None,
) -> ActivityInterval:
    return ActivityInterval(
        provider_interval_id=None,
        interval_type="WORK",
        label=None,
        start_index=start,
        end_index=end,
        start_time_seconds=start,
        end_time_seconds=start + duration,
        distance_m=distance,
        moving_time_seconds=duration,
        elapsed_time_seconds=duration,
        average_speed_mps=speed,
    )


def prescription(
    *,
    repetitions: int = 4,
) -> IntervalSetPrescription:
    return IntervalSetPrescription(
        repetitions=repetitions,
        work_distance_m=100.0,
        recovery_duration_seconds=45.0,
        repetition_target=RepetitionTarget(
            distance_m=100.0,
            target_duration_min_seconds=20.0,
            target_duration_max_seconds=24.0,
            vma_kmh=15.0,
            vma_percent_min=100.0,
            vma_percent_max=115.0,
        ),
    )


def test_detects_expected_repetitions() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=(
            interval(
                start=0,
                end=20,
                distance=100,
                duration=22,
            ),
            interval(
                start=70,
                end=90,
                distance=101,
                duration=22,
            ),
            interval(
                start=140,
                end=160,
                distance=99,
                duration=21,
            ),
            interval(
                start=210,
                end=230,
                distance=100,
                duration=23,
            ),
        ),
    )

    result = detect_repetitions(
        detail,
        prescription(),
    )

    assert result.detected_repetitions == 4
    assert result.expected_repetitions == 4
    assert result.is_complete is True


def test_rejects_irrelevant_intervals() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=(
            interval(
                start=0,
                end=100,
                distance=500,
                duration=180,
            ),
            interval(
                start=110,
                end=130,
                distance=100,
                duration=22,
            ),
            interval(
                start=180,
                end=200,
                distance=100,
                duration=22,
            ),
        ),
    )

    result = detect_repetitions(
        detail,
        prescription(
            repetitions=2,
        ),
    )

    assert result.detected_repetitions == 2

    assert [
        repetition.distance_m
        for repetition in result.repetitions
    ] == [
        100,
        100,
    ]


def test_overlapping_intervals_are_not_selected_together() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=(
            interval(
                start=0,
                end=30,
                distance=100,
                duration=22,
            ),
            interval(
                start=10,
                end=25,
                distance=100,
                duration=22,
            ),
            interval(
                start=70,
                end=90,
                distance=100,
                duration=22,
            ),
        ),
    )

    result = detect_repetitions(
        detail,
        prescription(
            repetitions=3,
        ),
    )

    assert result.detected_repetitions == 2

    first = result.repetitions[0]
    second = result.repetitions[1]

    assert (
        first.end_index
        < second.start_index
    )


def test_prefers_better_matching_overlap() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=(
            interval(
                start=0,
                end=20,
                distance=81,
                duration=25,
            ),
            interval(
                start=5,
                end=25,
                distance=100,
                duration=22,
            ),
            interval(
                start=70,
                end=90,
                distance=100,
                duration=22,
            ),
        ),
    )

    result = detect_repetitions(
        detail,
        prescription(
            repetitions=2,
        ),
    )

    assert result.detected_repetitions == 2

    assert (
        result.repetitions[0].distance_m
        == 100
    )


def test_distance_outside_tolerance_is_rejected() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=(
            interval(
                start=0,
                end=20,
                distance=79,
                duration=22,
            ),
            interval(
                start=70,
                end=90,
                distance=100,
                duration=22,
            ),
        ),
    )

    result = detect_repetitions(
        detail,
        prescription(
            repetitions=2,
        ),
    )

    assert result.detected_repetitions == 1


def test_duration_outside_tolerance_is_rejected() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=(
            interval(
                start=0,
                end=20,
                distance=100,
                duration=31,
            ),
            interval(
                start=70,
                end=90,
                distance=100,
                duration=22,
            ),
        ),
    )

    result = detect_repetitions(
        detail,
        prescription(
            repetitions=2,
        ),
    )

    assert result.detected_repetitions == 1


def test_chronological_order_is_preserved() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=(
            interval(
                start=200,
                end=220,
                distance=100,
                duration=22,
            ),
            interval(
                start=0,
                end=20,
                distance=100,
                duration=22,
            ),
            interval(
                start=100,
                end=120,
                distance=100,
                duration=22,
            ),
        ),
    )

    result = detect_repetitions(
        detail,
        prescription(
            repetitions=3,
        ),
    )

    assert [
        repetition.start_index
        for repetition in result.repetitions
    ] == [
        0,
        100,
        200,
    ]


def test_detection_stops_at_prescribed_count() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=tuple(
            interval(
                start=index * 70,
                end=index * 70 + 20,
                distance=100,
                duration=22,
            )
            for index in range(6)
        ),
    )

    result = detect_repetitions(
        detail,
        prescription(
            repetitions=4,
        ),
    )

    assert result.detected_repetitions == 4


def test_duration_based_prescription_is_supported() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        intervals=(
            interval(
                start=0,
                end=300,
                distance=1000,
                duration=300,
            ),
            interval(
                start=420,
                end=720,
                distance=1000,
                duration=305,
            ),
        ),
    )

    result = detect_repetitions(
        detail,
        IntervalSetPrescription(
            repetitions=2,
            work_duration_seconds=300.0,
            recovery_duration_seconds=120.0,
        ),
    )

    assert result.detected_repetitions == 2


def test_empty_activity_detail_returns_empty_result() -> None:
    result = detect_repetitions(
        ActivityDetail(
            provider_activity_id="i1",
        ),
        prescription(),
    )

    assert result.detected_repetitions == 0
    assert result.is_complete is False
