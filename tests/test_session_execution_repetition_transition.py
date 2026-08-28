from opencoach.training.session_execution import (
    IntervalSetPrescription,
    StreamRepetitionCandidate,
    score_repetition_transition,
)


def candidate(
    start: float,
    end: float,
) -> StreamRepetitionCandidate:
    duration = (
        end - start
    )

    return StreamRepetitionCandidate(
        start_index=int(start),
        end_index=int(end),
        start_time_seconds=start,
        end_time_seconds=end,
        distance_m=300.0,
        duration_seconds=duration,
        average_speed_mps=(
            300.0 / duration
        ),
        match_score=1.0,
    )


def prescription() -> IntervalSetPrescription:
    return IntervalSetPrescription(
        repetitions=7,
        work_distance_m=300.0,
        recovery_duration_seconds=60.0,
    )


def test_exact_60_second_recovery_scores_one() -> None:
    result = score_repetition_transition(
        candidate(
            0.0,
            70.0,
        ),
        candidate(
            130.0,
            200.0,
        ),
        prescription(),
    )

    assert (
        result.recovery_duration_seconds
        == 60.0
    )

    assert result.recovery_score == 1.0


def test_54_second_recovery_remains_high() -> None:
    result = score_repetition_transition(
        candidate(
            0.0,
            70.0,
        ),
        candidate(
            124.0,
            194.0,
        ),
        prescription(),
    )

    assert result.recovery_score == 0.9


def test_72_second_recovery_is_still_good() -> None:
    result = score_repetition_transition(
        candidate(
            0.0,
            70.0,
        ),
        candidate(
            142.0,
            212.0,
        ),
        prescription(),
    )

    assert result.recovery_score == 0.8


def test_24_second_recovery_scores_low() -> None:
    result = score_repetition_transition(
        candidate(
            0.0,
            70.0,
        ),
        candidate(
            94.0,
            164.0,
        ),
        prescription(),
    )

    assert result.recovery_score == 0.4


def test_90_second_recovery_scores_half() -> None:
    result = score_repetition_transition(
        candidate(
            0.0,
            70.0,
        ),
        candidate(
            160.0,
            230.0,
        ),
        prescription(),
    )

    assert result.recovery_score == 0.5


def test_recovery_is_guidance_not_hard_filter() -> None:
    result = score_repetition_transition(
        candidate(
            0.0,
            70.0,
        ),
        candidate(
            190.0,
            260.0,
        ),
        prescription(),
    )

    assert (
        result.recovery_duration_seconds
        == 120.0
    )

    assert result.recovery_score == 0.0

    # La transition reste représentable :
    # le comparateur pourra ensuite dire que
    # la récupération n'a pas été respectée.
    assert result.is_valid is True
