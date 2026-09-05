from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)

import pytest

from opencoach.coaching.weekly_debrief_eligibility import (
    WeeklyClosureEligibility,
    evaluate_weekly_closure_eligibility,
)


SUNDAY = date(2026, 9, 6)
TZ = timezone(
    timedelta(hours=2)
)


def dt(
    hour: int,
    minute: int = 0,
    *,
    day: int = 6,
) -> datetime:
    return datetime(
        2026,
        9,
        day,
        hour,
        minute,
        tzinfo=TZ,
    )


def test_before_sunday_waits() -> None:
    result = (
        evaluate_weekly_closure_eligibility(
            now=dt(
                22,
                day=5,
            ),
            week_end=SUNDAY,
            has_remaining_planned_session=False,
        )
    )

    assert (
        result.decision
        is WeeklyClosureEligibility.WAIT
    )


def test_sunday_before_20h_waits() -> None:
    result = (
        evaluate_weekly_closure_eligibility(
            now=dt(19, 59),
            week_end=SUNDAY,
            has_remaining_planned_session=False,
        )
    )

    assert (
        result.decision
        is WeeklyClosureEligibility.WAIT
    )


def test_remaining_sunday_session_waits() -> None:
    result = (
        evaluate_weekly_closure_eligibility(
            now=dt(21, 0),
            week_end=SUNDAY,
            has_remaining_planned_session=True,
        )
    )

    assert (
        result.decision
        is WeeklyClosureEligibility.WAIT
    )


def test_recent_completion_waits_for_sync_grace() -> None:
    result = (
        evaluate_weekly_closure_eligibility(
            now=dt(21, 10),
            week_end=SUNDAY,
            has_remaining_planned_session=False,
            last_completed_at=dt(21, 0),
        )
    )

    assert (
        result.decision
        is WeeklyClosureEligibility.WAIT
    )
    assert "5 min" in result.reason


def test_exact_sync_grace_can_close() -> None:
    result = (
        evaluate_weekly_closure_eligibility(
            now=dt(21, 15),
            week_end=SUNDAY,
            has_remaining_planned_session=False,
            last_completed_at=dt(21, 0),
        )
    )

    assert (
        result.decision
        is WeeklyClosureEligibility.CLOSE
    )


def test_normal_sunday_closure() -> None:
    result = (
        evaluate_weekly_closure_eligibility(
            now=dt(20, 30),
            week_end=SUNDAY,
            has_remaining_planned_session=False,
        )
    )

    assert (
        result.decision
        is WeeklyClosureEligibility.CLOSE
    )


def test_cutoff_overrides_remaining_session() -> None:
    result = (
        evaluate_weekly_closure_eligibility(
            now=dt(23, 45),
            week_end=SUNDAY,
            has_remaining_planned_session=True,
        )
    )

    assert (
        result.decision
        is WeeklyClosureEligibility.CUTOFF
    )


def test_after_sunday_is_cutoff() -> None:
    result = (
        evaluate_weekly_closure_eligibility(
            now=dt(
                0,
                10,
                day=7,
            ),
            week_end=SUNDAY,
            has_remaining_planned_session=False,
        )
    )

    assert (
        result.decision
        is WeeklyClosureEligibility.CUTOFF
    )


def test_naive_now_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        evaluate_weekly_closure_eligibility(
            now=datetime(
                2026,
                9,
                6,
                21,
                0,
            ),
            week_end=SUNDAY,
            has_remaining_planned_session=False,
        )


def test_future_completion_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="postérieur à now",
    ):
        evaluate_weekly_closure_eligibility(
            now=dt(21, 0),
            week_end=SUNDAY,
            has_remaining_planned_session=False,
            last_completed_at=dt(21, 1),
        )
