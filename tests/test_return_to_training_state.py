from datetime import date

from opencoach.planning.return_to_training_policy import (
    ReturnToTrainingPolicy,
)
from opencoach.planning.return_to_training_state import (
    calculate_return_to_training_state,
)


def create_policy(
    minimum_weeks: int = 3,
) -> ReturnToTrainingPolicy:
    return ReturnToTrainingPolicy(
        minimum_weeks=minimum_weeks,
        reason="Test.",
    )


def test_return_starts_day_after_event() -> None:
    state = calculate_return_to_training_state(
        planning_date=date(
            2027,
            3,
            15,
        ),
        event_end_date=date(
            2027,
            3,
            14,
        ),
        policy=create_policy(),
    )

    assert state.active is True
    assert state.week_index == 1
    assert state.return_start_date == date(
        2027,
        3,
        15,
    )


def test_date_during_event_is_not_return_phase() -> None:
    state = calculate_return_to_training_state(
        planning_date=date(
            2027,
            3,
            10,
        ),
        event_end_date=date(
            2027,
            3,
            14,
        ),
        policy=create_policy(),
    )

    assert state.active is False
    assert state.week_index is None
    assert state.minimum_completed is False


def test_second_return_week_is_detected() -> None:
    state = calculate_return_to_training_state(
        planning_date=date(
            2027,
            3,
            22,
        ),
        event_end_date=date(
            2027,
            3,
            14,
        ),
        policy=create_policy(),
    )

    assert state.active is True
    assert state.week_index == 2


def test_last_minimum_week_is_still_active() -> None:
    state = calculate_return_to_training_state(
        planning_date=date(
            2027,
            4,
            4,
        ),
        event_end_date=date(
            2027,
            3,
            14,
        ),
        policy=create_policy(),
    )

    assert state.active is True
    assert state.week_index == 3
    assert state.minimum_completed is False


def test_minimum_period_completes_after_three_weeks() -> None:
    state = calculate_return_to_training_state(
        planning_date=date(
            2027,
            4,
            5,
        ),
        event_end_date=date(
            2027,
            3,
            14,
        ),
        policy=create_policy(),
    )

    assert state.active is False
    assert state.minimum_completed is True


def test_one_week_policy_completes_after_seven_days() -> None:
    state = calculate_return_to_training_state(
        planning_date=date(
            2027,
            3,
            22,
        ),
        event_end_date=date(
            2027,
            3,
            14,
        ),
        policy=create_policy(
            minimum_weeks=1,
        ),
    )

    assert state.active is False
    assert state.minimum_completed is True
