from types import SimpleNamespace

from opencoach.coaching.generation.context import (
    WeeklyPlanningContextBuilder,
)
from opencoach.planning.return_to_training.clearance import (
    ReadinessAnswer,
)


def create_context(
    *,
    level="good",
    critical_count=0,
    training_constraints=(),
):
    readiness = SimpleNamespace(
        level=level,
        critical_count=critical_count,
        training_constraints=training_constraints,
    )

    assessment = SimpleNamespace(
        readiness=readiness,
    )

    return SimpleNamespace(
        readiness=assessment,
    )


def test_missing_readiness_keeps_return_state_unknown() -> None:
    context = SimpleNamespace(
        readiness=None,
    )

    result = (
        WeeklyPlanningContextBuilder
        ._return_to_training_readiness(
            context
        )
    )

    assert (
        result.blocking_symptoms
        is ReadinessAnswer.UNKNOWN
    )

    assert (
        result.recovery_sufficient
        is ReadinessAnswer.UNKNOWN
    )

    assert (
        result.clearance_confirmed
        is ReadinessAnswer.UNKNOWN
    )


def test_good_objective_readiness_does_not_confirm_recovery() -> None:
    result = (
        WeeklyPlanningContextBuilder
        ._return_to_training_readiness(
            create_context(
                level="good",
            )
        )
    )

    assert (
        result.recovery_sufficient
        is ReadinessAnswer.UNKNOWN
    )


def test_low_readiness_marks_recovery_insufficient() -> None:
    result = (
        WeeklyPlanningContextBuilder
        ._return_to_training_readiness(
            create_context(
                level="low",
            )
        )
    )

    assert (
        result.recovery_sufficient
        is ReadinessAnswer.NO
    )


def test_critical_signal_marks_recovery_insufficient() -> None:
    result = (
        WeeklyPlanningContextBuilder
        ._return_to_training_readiness(
            create_context(
                level="moderate",
                critical_count=1,
            )
        )
    )

    assert (
        result.recovery_sufficient
        is ReadinessAnswer.NO
    )


def test_recovery_constraint_marks_recovery_insufficient() -> None:
    result = (
        WeeklyPlanningContextBuilder
        ._return_to_training_readiness(
            create_context(
                level="moderate",
                training_constraints=(
                    "prefer_recovery_or_rest",
                ),
            )
        )
    )

    assert (
        result.recovery_sufficient
        is ReadinessAnswer.NO
    )


def test_objective_readiness_never_clears_symptoms() -> None:
    result = (
        WeeklyPlanningContextBuilder
        ._return_to_training_readiness(
            create_context(
                level="high",
            )
        )
    )

    assert (
        result.blocking_symptoms
        is ReadinessAnswer.UNKNOWN
    )

    assert (
        result.clearance_confirmed
        is ReadinessAnswer.UNKNOWN
    )
