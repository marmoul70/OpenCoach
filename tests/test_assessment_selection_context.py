from opencoach.planning import (
    AssessmentSafetyContext,
    build_assessment_selection_context,
)


def test_selection_context_inherits_safety_decision() -> None:
    safety = AssessmentSafetyContext(
        maximal_testing_allowed=False,
        blocking_reasons=(
            "Readiness insuffisant.",
        ),
        warnings=(),
        days_to_primary_race=None,
    )

    context = build_assessment_selection_context(
        safety=safety,
        track_available=True,
        flat_route_available=True,
    )

    assert (
        context.maximal_testing_allowed
        is False
    )

    assert context.track_available is True
    assert context.flat_route_available is True


def test_selection_context_preserves_environment_availability() -> None:
    safety = AssessmentSafetyContext(
        maximal_testing_allowed=True,
        blocking_reasons=(),
        warnings=(),
        days_to_primary_race=30,
    )

    context = build_assessment_selection_context(
        safety=safety,
        track_available=False,
        flat_route_available=True,
        laboratory_available=True,
    )

    assert (
        context.maximal_testing_allowed
        is True
    )

    assert context.track_available is False
    assert context.flat_route_available is True
    assert context.laboratory_available is True
