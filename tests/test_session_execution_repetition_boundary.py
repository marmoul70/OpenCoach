from opencoach.models import (
    ActivityDetail,
    ActivityStream,
    ActivityStreams,
)
from opencoach.training.session_execution import (
    IntervalSetPrescription,
    StreamRepetitionCandidate,
    refine_repetition_boundary,
)


def prescription() -> IntervalSetPrescription:
    return IntervalSetPrescription(
        repetitions=7,
        work_distance_m=300.0,
        recovery_duration_seconds=60.0,
    )


def candidate(
    start=55.0,
    end=135.0,
) -> StreamRepetitionCandidate:
    return StreamRepetitionCandidate(
        start_index=int(start),
        end_index=int(end),
        start_time_seconds=start,
        end_time_seconds=end,
        distance_m=300.0,
        duration_seconds=end - start,
        average_speed_mps=(
            300.0
            / (end - start)
        ),
        match_score=1.0,
    )


def activity(
    *,
    real_start=60,
    real_end=130,
    watts=True,
) -> ActivityDetail:
    times = tuple(
        range(200)
    )

    speed_values = []
    cadence_values = []
    watts_values = []

    for second in times:
        work = (
            real_start
            <= second
            < real_end
        )

        speed_values.append(
            4.4 if work else 1.8
        )

        cadence_values.append(
            96.0 if work else 70.0
        )

        watts_values.append(
            360.0 if work else 140.0
        )

    return ActivityDetail(
        provider_activity_id="test",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=times,
            ),
            velocity_smooth=ActivityStream(
                stream_type="velocity_smooth",
                data=tuple(speed_values),
            ),
            cadence=ActivityStream(
                stream_type="cadence",
                data=tuple(cadence_values),
            ),
            watts=(
                ActivityStream(
                    stream_type="watts",
                    data=tuple(watts_values),
                )
                if watts
                else None
            ),
        ),
    )


def test_refines_shifted_boundaries() -> None:
    result = refine_repetition_boundary(
        activity(),
        candidate(),
        prescription(),
    )

    assert (
        57.0
        <= result.start_time_seconds
        <= 62.0
    )

    assert (
        127.0
        <= result.end_time_seconds
        <= 132.0
    )

    assert result.start_shift_seconds > 0
    assert result.end_shift_seconds < 0

    assert result.confidence >= 0.8


def test_missing_watts_still_uses_speed_and_cadence() -> None:
    result = refine_repetition_boundary(
        activity(
            watts=False,
        ),
        candidate(),
        prescription(),
    )

    assert (
        57.0
        <= result.start_time_seconds
        <= 62.0
    )

    assert (
        127.0
        <= result.end_time_seconds
        <= 132.0
    )


def test_no_metrics_keeps_original_boundary() -> None:
    detail = ActivityDetail(
        provider_activity_id="test",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=tuple(
                    range(200)
                ),
            ),
        ),
    )

    original = candidate()

    result = refine_repetition_boundary(
        detail,
        original,
        prescription(),
    )

    assert (
        result.start_time_seconds
        == original.start_time_seconds
    )

    assert (
        result.end_time_seconds
        == original.end_time_seconds
    )

    assert result.confidence == 0.0


def test_planned_recovery_does_not_force_boundary() -> None:
    result = refine_repetition_boundary(
        activity(
            real_start=70,
            real_end=125,
        ),
        candidate(
            start=55,
            end=135,
        ),
        prescription(),
    )

    assert (
        result.start_time_seconds
        >= 67.0
    )

    assert (
        result.end_time_seconds
        <= 128.0
    )

    # Même si le planning connaît 60 s de récupération,
    # les frontières suivent les signaux réalisés.
    assert (
        result.duration_seconds
        < 65.0
    )
