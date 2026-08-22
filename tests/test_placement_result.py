from datetime import date

from opencoach.planning import (
    SessionPlacementCandidate,
    build_session_placement_result,
)


def create_candidate(
    *,
    target_date: date,
    score: int,
    eligible: bool,
) -> SessionPlacementCandidate:
    return SessionPlacementCandidate(
        date=target_date,
        calendar_score=score,
        placement_score=score,
        eligible=eligible,
        preferred=True,
        requires_confirmation=False,
        running_allowed=True,
        cross_training_allowed=True,
        max_duration_minutes=None,
        rules=(),
        reasons=(),
    )


def test_separates_eligible_and_rejected_candidates() -> None:
    first = create_candidate(
        target_date=date(
            2026,
            8,
            25,
        ),
        score=90,
        eligible=True,
    )

    rejected = create_candidate(
        target_date=date(
            2026,
            8,
            27,
        ),
        score=80,
        eligible=False,
    )

    second = create_candidate(
        target_date=date(
            2026,
            8,
            29,
        ),
        score=70,
        eligible=True,
    )

    result = build_session_placement_result(
        (
            first,
            second,
            rejected,
        )
    )

    assert result.eligible_candidates == (
        first,
        second,
    )

    assert result.rejected_candidates == (
        rejected,
    )


def test_best_candidate_is_first_eligible_candidate() -> None:
    first = create_candidate(
        target_date=date(
            2026,
            8,
            25,
        ),
        score=90,
        eligible=True,
    )

    second = create_candidate(
        target_date=date(
            2026,
            8,
            29,
        ),
        score=70,
        eligible=True,
    )

    result = build_session_placement_result(
        (
            first,
            second,
        )
    )

    assert result.best_candidate is first
    assert result.has_solution is True


def test_no_solution_when_every_candidate_is_rejected() -> None:
    rejected = create_candidate(
        target_date=date(
            2026,
            8,
            27,
        ),
        score=80,
        eligible=False,
    )

    result = build_session_placement_result(
        (
            rejected,
        )
    )

    assert result.eligible_candidates == ()
    assert result.rejected_candidates == (
        rejected,
    )

    assert result.best_candidate is None
    assert result.has_solution is False


def test_empty_candidates_has_no_solution() -> None:
    result = build_session_placement_result(
        ()
    )

    assert result.eligible_candidates == ()
    assert result.rejected_candidates == ()

    assert result.best_candidate is None
    assert result.has_solution is False
