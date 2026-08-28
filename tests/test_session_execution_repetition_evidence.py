from opencoach.models import (
    ActivityDetail,
    ActivityStream,
    ActivityStreams,
)
from opencoach.training.session_execution import (
    IntervalSetPrescription,
    RepetitionTarget,
    StreamRepetitionCandidate,
    score_repetition_candidate,
)


def candidate() -> StreamRepetitionCandidate:
    return StreamRepetitionCandidate(
        start_index=60,
        end_index=130,
        start_time_seconds=60.0,
        end_time_seconds=130.0,
        distance_m=300.0,
        duration_seconds=70.0,
        average_speed_mps=(
            300.0 / 70.0
        ),
        match_score=1.0,
    )


def prescription() -> IntervalSetPrescription:
    return IntervalSetPrescription(
        repetitions=7,
        work_distance_m=300.0,
        recovery_duration_seconds=60.0,
        repetition_target=RepetitionTarget(
            distance_m=300.0,
            target_duration_min_seconds=65.0,
            target_duration_max_seconds=75.0,
        ),
    )


def streams(
    *,
    work_speed=4.3,
    recovery_speed=2.0,
    work_cadence=95.0,
    recovery_cadence=75.0,
    work_watts=350.0,
    recovery_watts=180.0,
    flat_hr=False,
    include_watts=True,
) -> ActivityDetail:
    times = tuple(
        range(0, 200)
    )

    speed = []
    cadence = []
    watts = []
    hr = []

    for second in times:
        in_work = (
            60
            <= second
            < 130
        )

        speed.append(
            work_speed
            if in_work
            else recovery_speed
        )

        cadence.append(
            work_cadence
            if in_work
            else recovery_cadence
        )

        watts.append(
            work_watts
            if in_work
            else recovery_watts
        )

        if flat_hr:
            hr.append(140.0)
        elif second < 60:
            hr.append(130.0)
        elif second < 130:
            hr.append(
                min(
                    155.0,
                    130.0
                    + (
                        second - 60
                    )
                    * 0.5,
                )
            )
        else:
            hr.append(150.0)

    return ActivityDetail(
        provider_activity_id="i1",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=times,
            ),
            velocity_smooth=ActivityStream(
                stream_type="velocity_smooth",
                data=tuple(speed),
            ),
            cadence=ActivityStream(
                stream_type="cadence",
                data=tuple(cadence),
            ),
            watts=(
                ActivityStream(
                    stream_type="watts",
                    data=tuple(watts),
                )
                if include_watts
                else None
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=tuple(hr),
            ),
        ),
    )


def test_strong_multisignal_candidate_has_high_confidence() -> None:
    result = score_repetition_candidate(
        streams(),
        candidate(),
        prescription(),
    )

    assert result.duration_score == 1.0
    assert result.speed_contrast_score == 1.0
    assert result.cadence_score == 1.0
    assert result.watts_score == 1.0

    assert (
        result.heart_rate_score
        is not None
    )

    assert result.confidence >= 0.90


def test_missing_watts_does_not_penalize_candidate() -> None:
    result = score_repetition_candidate(
        streams(
            include_watts=False,
        ),
        candidate(),
        prescription(),
    )

    assert result.watts_score is None

    assert (
        "watts"
        not in result.available_signals
    )

    assert result.confidence >= 0.85


def test_flat_recovery_contrast_reduces_confidence() -> None:
    result = score_repetition_candidate(
        streams(
            work_speed=3.0,
            recovery_speed=2.9,
            work_cadence=82.0,
            recovery_cadence=80.0,
            work_watts=220.0,
            recovery_watts=210.0,
            flat_hr=True,
        ),
        candidate(),
        prescription(),
    )

    assert (
        result.speed_contrast_score
        < 0.20
    )

    assert result.cadence_score < 0.50
    assert result.watts_score < 0.50
    assert result.heart_rate_score == 0.0

    assert result.confidence < 0.60


def test_short_repetition_can_be_valid_with_flat_hr() -> None:
    result = score_repetition_candidate(
        streams(
            flat_hr=True,
        ),
        candidate(),
        prescription(),
    )

    assert result.heart_rate_score == 0.0

    # La FC n'est qu'un soutien sur une fraction courte.
    assert result.confidence >= 0.80


def test_duration_outside_target_reduces_evidence() -> None:
    slow_candidate = StreamRepetitionCandidate(
        start_index=60,
        end_index=145,
        start_time_seconds=60.0,
        end_time_seconds=145.0,
        distance_m=300.0,
        duration_seconds=85.0,
        average_speed_mps=(
            300.0 / 85.0
        ),
        match_score=0.8,
    )

    result = score_repetition_candidate(
        streams(),
        slow_candidate,
        prescription(),
    )

    assert (
        result.duration_score
        is not None
    )

    assert result.duration_score < 1.0


def test_only_available_signals_are_used() -> None:
    detail = ActivityDetail(
        provider_activity_id="i1",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=tuple(
                    range(200)
                ),
            ),
        ),
    )

    result = score_repetition_candidate(
        detail,
        candidate(),
        prescription(),
    )

    assert result.speed_contrast_score is None
    assert result.cadence_score is None
    assert result.watts_score is None
    assert result.heart_rate_score is None

    assert result.available_signals == (
        "duration",
    )

    assert result.confidence == 1.0
