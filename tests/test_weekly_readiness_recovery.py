from types import SimpleNamespace

from opencoach.coaching.generation.context import (
    WeeklyPlanningContextBuilder,
)


def _context_with_readiness(
    *,
    level: str,
    critical_count: int = 0,
    constraints: tuple[str, ...] = (),
):
    daily_readiness = SimpleNamespace(
        level=level,
        critical_count=critical_count,
        training_constraints=constraints,
    )

    assessment = SimpleNamespace(
        readiness=daily_readiness,
    )

    return SimpleNamespace(
        readiness=assessment,
    )


def test_missing_readiness_does_not_force_recovery() -> None:
    context = SimpleNamespace(
        readiness=None,
    )

    assert not (
        WeeklyPlanningContextBuilder
        ._fatigue_requires_recovery(
            context
        )
    )


def test_good_readiness_does_not_force_recovery() -> None:
    context = _context_with_readiness(
        level="good",
    )

    assert not (
        WeeklyPlanningContextBuilder
        ._fatigue_requires_recovery(
            context
        )
    )


def test_recovery_constraint_forces_recovery() -> None:
    context = _context_with_readiness(
        level="moderate",
        constraints=(
            "prefer_recovery_or_rest",
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._fatigue_requires_recovery(
            context
        )
    )


def test_critical_signal_forces_recovery() -> None:
    context = _context_with_readiness(
        level="moderate",
        critical_count=1,
    )

    assert (
        WeeklyPlanningContextBuilder
        ._fatigue_requires_recovery(
            context
        )
    )


def test_low_readiness_forces_recovery() -> None:
    context = _context_with_readiness(
        level="low",
    )

    assert (
        WeeklyPlanningContextBuilder
        ._fatigue_requires_recovery(
            context
        )
    )


def test_multi_day_illness_forces_weekly_recovery() -> None:
    from datetime import date
    from uuid import uuid4

    from opencoach.models import (
        AthleteConstraint,
    )

    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2026,
            8,
            27,
        ),
        constraint_type="illness",
        availability="unavailable",
        running_allowed=False,
        cross_training_allowed=False,
    )

    context = SimpleNamespace(
        planning_date=date(
            2026,
            8,
            25,
        ),
        readiness=None,
        constraints=(
            constraint,
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._fatigue_requires_recovery(
            context
        )
    )


def test_work_absence_does_not_force_weekly_recovery() -> None:
    from datetime import date
    from uuid import uuid4

    from opencoach.models import (
        AthleteConstraint,
    )

    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
        constraint_type="work",
        availability="unavailable",
        running_allowed=False,
        cross_training_allowed=False,
    )

    context = SimpleNamespace(
        planning_date=date(
            2026,
            8,
            25,
        ),
        readiness=None,
        constraints=(
            constraint,
        ),
    )

    assert not (
        WeeklyPlanningContextBuilder
        ._fatigue_requires_recovery(
            context
        )
    )
