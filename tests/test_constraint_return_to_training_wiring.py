from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from opencoach.coaching.generation.context import (
    WeeklyPlanningContextBuilder,
)
from opencoach.models import (
    AthleteConstraint,
)
from opencoach.planning.trajectory.adjustment import (
    ProgressionAdjustment,
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


def test_finished_long_illness_builds_return_to_training_adjustment(
) -> None:
    illness = _constraint(
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
            illness,
        ),
    )

    adjustments = (
        WeeklyPlanningContextBuilder
        ._constraint_adjustments(
            context
        )
    )

    assert len(
        adjustments
    ) == 1

    adjustment = adjustments[0]

    assert adjustment.requires_return_to_training

    assert (
        adjustment.progression
        is ProgressionAdjustment.REBUILD
    )

    assert not adjustment.allow_schedule_compression


def test_active_long_illness_does_not_start_return_to_training(
) -> None:
    illness = _constraint(
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
            illness,
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._constraint_adjustments(
            context
        )
        == ()
    )


def test_short_illness_does_not_rebuild_progression() -> None:
    illness = _constraint(
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
            illness,
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._constraint_adjustments(
            context
        )
        == ()
    )


def test_work_absence_does_not_start_return_to_training() -> None:
    work = _constraint(
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
            work,
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._constraint_adjustments(
            context
        )
        == ()
    )


def test_travel_does_not_start_return_to_training() -> None:
    travel = _constraint(
        constraint_type="travel",
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
            travel,
        ),
    )

    assert (
        WeeklyPlanningContextBuilder
        ._constraint_adjustments(
            context
        )
        == ()
    )
