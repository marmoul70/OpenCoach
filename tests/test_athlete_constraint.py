from datetime import date
from uuid import uuid4

import pytest

from opencoach.models import AthleteConstraint


def test_constraint_is_active_inside_period() -> None:
    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=date(2026, 8, 24),
        end_date=date(2026, 8, 30),
        constraint_type="injury",
        availability="limited",
        running_allowed=False,
        cross_training_allowed=True,
    )

    assert constraint.is_active_on(
        date(2026, 8, 27)
    )


def test_constraint_is_active_on_boundaries() -> None:
    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=date(2026, 8, 24),
        end_date=date(2026, 8, 30),
        constraint_type="work",
        availability="unavailable",
    )

    assert constraint.is_active_on(
        date(2026, 8, 24)
    )

    assert constraint.is_active_on(
        date(2026, 8, 30)
    )


def test_constraint_is_not_active_outside_period() -> None:
    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=date(2026, 8, 24),
        end_date=date(2026, 8, 30),
        constraint_type="travel",
        availability="unavailable",
    )

    assert not constraint.is_active_on(
        date(2026, 8, 23)
    )

    assert not constraint.is_active_on(
        date(2026, 8, 31)
    )


def test_constraint_rejects_invalid_date_range() -> None:
    with pytest.raises(
        ValueError,
        match="date de fin",
    ):
        AthleteConstraint(
            id=uuid4(),
            start_date=date(2026, 8, 30),
            end_date=date(2026, 8, 24),
            constraint_type="personal",
            availability="unavailable",
        )


def test_constraint_rejects_negative_max_duration() -> None:
    with pytest.raises(
        ValueError,
        match="durée maximale",
    ):
        AthleteConstraint(
            id=uuid4(),
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 24),
            constraint_type="work",
            availability="limited",
            max_duration_minutes=-1,
        )


def test_available_override_can_open_exceptional_day() -> None:
    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=date(2026, 8, 27),
        end_date=date(2026, 8, 27),
        constraint_type="personal",
        availability="available_override",
    )

    assert constraint.availability == (
        "available_override"
    )

    assert constraint.is_active_on(
        date(2026, 8, 27)
    )


def test_injury_can_forbid_running_but_allow_cross_training() -> None:
    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=date(2026, 8, 24),
        end_date=date(2026, 8, 30),
        constraint_type="injury",
        availability="limited",
        running_allowed=False,
        cross_training_allowed=True,
        notes="Pas de course pendant une semaine.",
    )

    assert constraint.running_allowed is False
    assert constraint.cross_training_allowed is True
