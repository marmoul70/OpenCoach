from opencoach.planning import (
    AssessmentNeed,
    AssessmentSafetyContext,
    AssessmentSelectionContext,
    build_assessment_recommendation,
    build_assessment_session_spec,
    select_assessment_protocol,
)


def create_need(
    assessment_type="vma_calibration",
    metrics=("vma",),
):
    return AssessmentNeed(
        assessment_type=assessment_type,
        priority="high",
        metrics=tuple(metrics),
        reason="Calibration nécessaire.",
    )


def create_safety(
    *,
    allowed=True,
):
    return AssessmentSafetyContext(
        maximal_testing_allowed=allowed,
        blocking_reasons=(
            ()
            if allowed
            else (
                "Test maximal actuellement interdit.",
            )
        ),
        warnings=(),
        days_to_primary_race=None,
    )


def create_recommendation(
    *,
    need,
    context,
    safety=None,
):
    if safety is None:
        safety = create_safety()

    selection = select_assessment_protocol(
        need=need,
        context=context,
    )

    return build_assessment_recommendation(
        need=need,
        safety=safety,
        selection=selection,
    )


def test_vameval_recommendation_becomes_session_spec() -> None:
    recommendation = create_recommendation(
        need=create_need(),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=True,
            flat_route_available=True,
        ),
    )

    session = build_assessment_session_spec(
        recommendation
    )

    assert session is not None

    assert session.protocol_id == "vameval"
    assert session.title == "Test VAMEVAL"

    assert session.sport_type == "run"
    assert session.intensity == "maximal"

    assert session.duration_minutes == 45

    assert session.priority == "high"

    assert (
        session.requires_maximal_effort
        is True
    )

    assert "vma" in session.covered_metrics


def test_half_cooper_becomes_session_spec_without_track() -> None:
    recommendation = create_recommendation(
        need=create_need(),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=False,
            flat_route_available=True,
        ),
    )

    session = build_assessment_session_spec(
        recommendation
    )

    assert session is not None

    assert (
        session.protocol_id
        == "half_cooper"
    )

    assert (
        session.title
        == "Test demi-Cooper"
    )


def test_deferred_recommendation_does_not_create_session() -> None:
    need = create_need()

    safety = create_safety(
        allowed=False
    )

    recommendation = create_recommendation(
        need=need,
        safety=safety,
        context=AssessmentSelectionContext(
            maximal_testing_allowed=False,
            track_available=True,
            flat_route_available=True,
        ),
    )

    session = build_assessment_session_spec(
        recommendation
    )

    assert session is None


def test_threshold_session_preserves_required_metric() -> None:
    recommendation = create_recommendation(
        need=create_need(
            assessment_type="threshold_calibration",
            metrics=(
                "threshold_heart_rate_2",
            ),
        ),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            flat_route_available=True,
            laboratory_available=False,
        ),
    )

    session = build_assessment_session_spec(
        recommendation
    )

    assert session is not None

    assert (
        session.protocol_id
        == "twenty_minute_threshold"
    )

    assert (
        "threshold_heart_rate_2"
        in session.covered_metrics
    )


def test_session_description_explains_calibration_goal() -> None:
    recommendation = create_recommendation(
        need=create_need(),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=True,
        ),
    )

    session = build_assessment_session_spec(
        recommendation
    )

    assert session is not None

    assert "vma" in session.description.lower()
