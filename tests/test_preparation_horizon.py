from datetime import date

import pytest

from opencoach.coaching.replanning.preparation_horizon import (
    resolve_preparation_horizon,
)


RACE_DATE = date(
    2027,
    2,
    7,
)


def test_day_before_preparation_is_still_maintenance() -> None:
    decision = resolve_preparation_horizon(
        planning_date=date(
            2026,
            10,
            24,
        ),
        target_race_date=RACE_DATE,
    )

    assert (
        decision.preparation_start_date
        == date(
            2026,
            10,
            25,
        )
    )

    assert (
        decision.preparation_started
        is False
    )


def test_preparation_starts_on_boundary_date() -> None:
    decision = resolve_preparation_horizon(
        planning_date=date(
            2026,
            10,
            25,
        ),
        target_race_date=RACE_DATE,
    )

    assert (
        decision.preparation_started
        is True
    )


def test_preparation_horizon_rejects_past_race() -> None:
    with pytest.raises(
        ValueError,
        match="postérieure",
    ):
        resolve_preparation_horizon(
            planning_date=RACE_DATE,
            target_race_date=RACE_DATE,
        )
