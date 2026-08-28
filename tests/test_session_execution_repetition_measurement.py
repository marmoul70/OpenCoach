from opencoach.models import (
    ActivityDetail,
    ActivityStream,
    ActivityStreams,
)
from opencoach.training.session_execution import (
    RefinedRepetitionBoundary,
    measure_refined_repetition,
)


def detail() -> ActivityDetail:
    times = tuple(
        float(value)
        for value in range(101)
    )

    distance = tuple(
        value * 4.0
        for value in times
    )

    speed = tuple(
        4.0
        for _ in times
    )

    hr = tuple(
        140.0 + value * 0.1
        for value in times
    )

    cadence = tuple(
        92.0
        for _ in times
    )

    watts = tuple(
        320.0
        for _ in times
    )

    return ActivityDetail(
        provider_activity_id="test",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=times,
            ),
            distance=ActivityStream(
                stream_type="distance",
                data=distance,
            ),
            velocity_smooth=ActivityStream(
                stream_type="velocity_smooth",
                data=speed,
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=hr,
            ),
            cadence=ActivityStream(
                stream_type="cadence",
                data=cadence,
            ),
            watts=ActivityStream(
                stream_type="watts",
                data=watts,
            ),
        ),
    )


def boundary(
    start=10.0,
    end=70.0,
) -> RefinedRepetitionBoundary:
    return RefinedRepetitionBoundary(
        start_time_seconds=start,
        end_time_seconds=end,
        duration_seconds=end - start,
        original_start_time_seconds=8.0,
        original_end_time_seconds=72.0,
        start_shift_seconds=start - 8.0,
        end_shift_seconds=end - 72.0,
        confidence=0.95,
    )


def test_measures_real_distance_between_boundaries() -> None:
    result = measure_refined_repetition(
        detail(),
        boundary(),
    )

    assert result.duration_seconds == 60.0
    assert result.distance_m == 240.0

    assert (
        result.average_speed_mps
        == 4.0
    )


def test_distance_uses_interpolation() -> None:
    result = measure_refined_repetition(
        detail(),
        boundary(
            start=10.5,
            end=70.25,
        ),
    )

    assert (
        result.distance_m
        == 239.0
    )


def test_measures_physiological_data() -> None:
    result = measure_refined_repetition(
        detail(),
        boundary(),
    )

    assert (
        result.average_heart_rate
        is not None
    )

    assert result.max_heart_rate == 146.9
    assert result.average_cadence == 92.0
    assert result.average_watts == 320.0


def test_missing_distance_falls_back_to_velocity() -> None:
    base = detail()

    without_distance = ActivityDetail(
        provider_activity_id="test",
        streams=ActivityStreams(
            time=base.streams.time,
            velocity_smooth=(
                base.streams.velocity_smooth
            ),
        ),
    )

    result = measure_refined_repetition(
        without_distance,
        boundary(),
    )

    assert result.distance_m is None
    assert result.average_speed_mps == 4.0


def test_invalid_boundary_is_rejected() -> None:
    invalid = RefinedRepetitionBoundary(
        start_time_seconds=70.0,
        end_time_seconds=60.0,
        duration_seconds=-10.0,
        original_start_time_seconds=70.0,
        original_end_time_seconds=60.0,
        start_shift_seconds=0.0,
        end_shift_seconds=0.0,
        confidence=0.0,
    )

    try:
        measure_refined_repetition(
            detail(),
            invalid,
        )

    except ValueError as exc:
        assert (
            "postérieure"
            in str(exc)
        )

    else:
        raise AssertionError(
            "ValueError attendu."
        )
