from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from opencoach.coaching.generation.context import (
    WeeklyPlanningContextBuilder,
)
from opencoach.models import AthleteConstraint
from opencoach.planning.trajectory.event import (
    TrajectoryEventType,
)


PLANNING_DATE = date(
    2026,
    8,
    25,
)


def _constraint(
    *,
    constraint_type: str,
    start_date: date,
    end_date: date,
) -> AthleteConstraint:
    return AthleteConstraint(
        id=uuid4(),
        start_date=start_date,
        end_date=end_date,
        constraint_type=constraint_type,  # type: ignore[arg-type]
        availability="unavailable",  # type: ignore[arg-type]
        running_allowed=False,
        cross_training_allowed=False,
    )


def test_finished_long_illness_becomes_trajectory_event(
) -> None:
    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            19,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    context = SimpleNamespace(
        planning_date=PLANNING_DATE,
        constraints=(
            constraint,
        ),
    )

    events = (
        WeeklyPlanningContextBuilder
        ._constraint_return_events(
            context
        )
    )

    assert len(events) == 1

    assert (
        events[0].event_type
        is TrajectoryEventType.ILLNESS
    )

    assert (
        events[0].start_date
        == constraint.start_date
    )

    assert (
        events[0].end_date
        == constraint.end_date
    )


def test_finished_long_injury_becomes_trajectory_event(
) -> None:
    constraint = _constraint(
        constraint_type="injury",
        start_date=date(
            2026,
            8,
            18,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    context = SimpleNamespace(
        planning_date=PLANNING_DATE,
        constraints=(
            constraint,
        ),
    )

    events = (
        WeeklyPlanningContextBuilder
        ._constraint_return_events(
            context
        )
    )

    assert len(events) == 1

    assert (
        events[0].event_type
        is TrajectoryEventType.INJURY
    )


def test_active_illness_does_not_become_return_event(
) -> None:
    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            22,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
    )

    context = SimpleNamespace(
        planning_date=PLANNING_DATE,
        constraints=(
            constraint,
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._constraint_return_events(
            context
        )
        == ()
    )


def test_short_illness_does_not_become_return_event(
) -> None:
    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            23,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    context = SimpleNamespace(
        planning_date=PLANNING_DATE,
        constraints=(
            constraint,
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._constraint_return_events(
            context
        )
        == ()
    )


def test_work_absence_never_becomes_return_event(
) -> None:
    constraint = _constraint(
        constraint_type="work",
        start_date=date(
            2026,
            8,
            17,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    context = SimpleNamespace(
        planning_date=PLANNING_DATE,
        constraints=(
            constraint,
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._constraint_return_events(
            context
        )
        == ()
    )
