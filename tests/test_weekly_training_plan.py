from datetime import date
from uuid import uuid4

import pytest

from opencoach.models import (
    WeeklyTrainingPlan,
)


def create_plan(
    **overrides,
) -> WeeklyTrainingPlan:
    values = {
        "id": None,
        "athlete_profile_id": uuid4(),
        "week_start": date(
            2026,
            8,
            24,
        ),
        "week_end": date(
            2026,
            8,
            30,
        ),
        "phase": "base",
        "week_type": "loading",
        "phase_week_index": 2,
        "target_load": 200.0,
        "load_min": 190.0,
        "load_max": 210.0,
        "reference_duration_minutes": 240.0,
        "target_duration_minutes": 250.0,
        "long_endurance_reference_minutes": 90.0,
        "schedule_pressure": "moderate",
        "athlete_schedule_constrained": False,
    }

    values.update(
        overrides
    )

    return WeeklyTrainingPlan(
        **values,
    )


def test_weekly_training_plan_exposes_load_target() -> None:
    plan = create_plan()

    assert plan.has_load_target is True
    assert plan.target_load == 200.0
    assert plan.load_min == 190.0
    assert plan.load_max == 210.0


def test_weekly_training_plan_without_target_has_no_load_target() -> None:
    plan = create_plan(
        target_load=None,
        load_min=None,
        load_max=None,
    )

    assert plan.has_load_target is False


def test_weekly_training_plan_rejects_invalid_week() -> None:
    with pytest.raises(
        ValueError,
        match="fin de semaine",
    ):
        create_plan(
            week_start=date(
                2026,
                8,
                30,
            ),
            week_end=date(
                2026,
                8,
                24,
            ),
        )


def test_weekly_training_plan_rejects_invalid_phase_week_index() -> None:
    with pytest.raises(
        ValueError,
        match="indice de semaine",
    ):
        create_plan(
            phase_week_index=0,
        )


def test_weekly_training_plan_rejects_negative_load() -> None:
    with pytest.raises(
        ValueError,
        match="charges hebdomadaires",
    ):
        create_plan(
            target_load=-1.0,
            load_min=None,
            load_max=None,
        )


def test_weekly_training_plan_rejects_target_outside_range() -> None:
    with pytest.raises(
        ValueError,
        match="plage autorisée",
    ):
        create_plan(
            target_load=220.0,
            load_min=190.0,
            load_max=210.0,
        )


def test_weekly_training_plan_rejects_invalid_duration() -> None:
    with pytest.raises(
        ValueError,
        match="durées hebdomadaires",
    ):
        create_plan(
            target_duration_minutes=0.0,
        )
