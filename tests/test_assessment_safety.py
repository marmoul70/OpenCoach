from datetime import date, timedelta
from uuid import uuid4

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    Race,
)
from opencoach.planning import (
    PlanningContext,
    build_assessment_safety_context,
)
from opencoach.readiness import (
    DailyReadiness,
    ReadinessAssessment,
)


PLANNING_DATE = date(
    2026,
    8,
    22,
)


def create_daily_readiness(
    *,
    level="good",
    warning_count=0,
    critical_count=0,
    training_constraints=(),
):
    return DailyReadiness(
        score=80.0,
        level=level,
        signals=(),
        warning_count=warning_count,
        critical_count=critical_count,
        training_constraints=tuple(
            training_constraints
        ),
        fitness_ctl=50.0,
        fatigue_atl=45.0,
        training_balance=5.0,
    )


def create_readiness(
    daily,
):
    class FakeReadinessAssessment:
        readiness = daily

    return FakeReadinessAssessment()


def create_context(
    *,
    readiness=None,
    primary_race=None,
    constraints=(),
):
    return PlanningContext(
        planning_date=PLANNING_DATE,
        athlete=AthleteProfile(),
        primary_race=primary_race,
        training_races=(),
        readiness=readiness,
        recent_load=None,
        recent_stats=None,
        constraints=tuple(
            constraints
        ),
        constraints_end_date=(
            PLANNING_DATE
            + timedelta(days=14)
        ),
    )


def test_good_readiness_allows_maximal_testing() -> None:
    context = create_context(
        readiness=create_readiness(
            create_daily_readiness()
        )
    )

    safety = build_assessment_safety_context(
        context
    )

    assert (
        safety.maximal_testing_allowed
        is True
    )

    assert safety.has_blockers is False


def test_low_readiness_blocks_maximal_testing() -> None:
    context = create_context(
        readiness=create_readiness(
            create_daily_readiness(
                level="low"
            )
        )
    )

    safety = build_assessment_safety_context(
        context
    )

    assert (
        safety.maximal_testing_allowed
        is False
    )

    assert any(
        "readiness"
        in reason.lower()
        for reason in safety.blocking_reasons
    )


def test_critical_readiness_signal_blocks_testing() -> None:
    context = create_context(
        readiness=create_readiness(
            create_daily_readiness(
                critical_count=1
            )
        )
    )

    safety = build_assessment_safety_context(
        context
    )

    assert (
        safety.maximal_testing_allowed
        is False
    )


def test_missing_readiness_warns_but_does_not_block() -> None:
    safety = build_assessment_safety_context(
        create_context(
            readiness=None
        )
    )

    assert (
        safety.maximal_testing_allowed
        is True
    )

    assert safety.warnings


def test_active_running_prohibition_blocks_testing() -> None:
    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=PLANNING_DATE,
        end_date=(
            PLANNING_DATE
            + timedelta(days=7)
        ),
        constraint_type="injury",
        availability="limited",
        running_allowed=False,
        cross_training_allowed=True,
        notes="Blessure.",
    )

    safety = build_assessment_safety_context(
        create_context(
            readiness=create_readiness(
                create_daily_readiness()
            ),
            constraints=(
                constraint,
            ),
        )
    )

    assert (
        safety.maximal_testing_allowed
        is False
    )


def test_future_constraint_does_not_block_today() -> None:
    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=(
            PLANNING_DATE
            + timedelta(days=3)
        ),
        end_date=(
            PLANNING_DATE
            + timedelta(days=5)
        ),
        constraint_type="work",
        availability="unavailable",
        running_allowed=False,
        cross_training_allowed=False,
    )

    safety = build_assessment_safety_context(
        create_context(
            readiness=create_readiness(
                create_daily_readiness()
            ),
            constraints=(
                constraint,
            ),
        )
    )

    assert (
        safety.maximal_testing_allowed
        is True
    )


def test_primary_race_within_seven_days_blocks_test() -> None:
    race = Race(
        id=uuid4(),
        date=(
            PLANNING_DATE
            + timedelta(days=5)
        ),
        name="Trail objectif",
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="planned",
    )

    safety = build_assessment_safety_context(
        create_context(
            readiness=create_readiness(
                create_daily_readiness()
            ),
            primary_race=race,
        )
    )

    assert (
        safety.maximal_testing_allowed
        is False
    )

    assert safety.days_to_primary_race == 5


def test_primary_race_far_away_does_not_block_test() -> None:
    race = Race(
        id=uuid4(),
        date=(
            PLANNING_DATE
            + timedelta(days=30)
        ),
        name="Trail objectif",
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="planned",
    )

    safety = build_assessment_safety_context(
        create_context(
            readiness=create_readiness(
                create_daily_readiness()
            ),
            primary_race=race,
        )
    )

    assert (
        safety.maximal_testing_allowed
        is True
    )

    assert safety.days_to_primary_race == 30
