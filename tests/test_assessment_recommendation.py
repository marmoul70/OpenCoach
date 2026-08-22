from opencoach.planning import (
    AssessmentNeed,
    AssessmentSafetyContext,
    AssessmentSelectionContext,
    build_assessment_recommendation,
    select_assessment_protocol,
)


def create_need() -> AssessmentNeed:
    return AssessmentNeed(
        assessment_type="vma_calibration",
        priority="high",
        metrics=("vma",),
        reason="VMA à recalibrer.",
    )


def create_safety(
    *,
    allowed: bool,
) -> AssessmentSafetyContext:
    return AssessmentSafetyContext(
        maximal_testing_allowed=allowed,
        blocking_reasons=(
            ()
            if allowed
            else (
                "Une course principale est trop proche.",
            )
        ),
        warnings=(),
        days_to_primary_race=(
            30
            if allowed
            else 5
        ),
    )


def test_safe_vameval_is_ready_to_schedule() -> None:
    need = create_need()

    safety = create_safety(
        allowed=True
    )

    selection = select_assessment_protocol(
        need=need,
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=True,
            flat_route_available=True,
        ),
    )

    recommendation = (
        build_assessment_recommendation(
            need=need,
            safety=safety,
            selection=selection,
        )
    )

    assert (
        recommendation.status
        == "ready_to_schedule"
    )

    assert (
        recommendation.ready_to_schedule
        is True
    )

    assert recommendation.protocol is not None

    assert (
        recommendation.protocol.protocol_id
        == "vameval"
    )


def test_safety_block_defers_assessment() -> None:
    need = create_need()

    safety = create_safety(
        allowed=False
    )

    selection = select_assessment_protocol(
        need=need,
        context=AssessmentSelectionContext(
            maximal_testing_allowed=False,
            track_available=True,
            flat_route_available=True,
        ),
    )

    recommendation = (
        build_assessment_recommendation(
            need=need,
            safety=safety,
            selection=selection,
        )
    )

    assert (
        recommendation.status
        == "deferred"
    )

    assert recommendation.protocol is None

    assert (
        recommendation.ready_to_schedule
        is False
    )

    assert recommendation.reasons == (
        "Une course principale est trop proche.",
    )


def test_missing_environment_reports_no_protocol() -> None:
    need = create_need()

    safety = create_safety(
        allowed=True
    )

    selection = select_assessment_protocol(
        need=need,
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=False,
            flat_route_available=False,
            laboratory_available=False,
        ),
    )

    recommendation = (
        build_assessment_recommendation(
            need=need,
            safety=safety,
            selection=selection,
        )
    )

    assert (
        recommendation.status
        == "no_protocol_available"
    )

    assert recommendation.protocol is None

    assert recommendation.reasons


def test_half_cooper_can_become_ready_without_track() -> None:
    need = create_need()

    safety = create_safety(
        allowed=True
    )

    selection = select_assessment_protocol(
        need=need,
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=False,
            flat_route_available=True,
        ),
    )

    recommendation = (
        build_assessment_recommendation(
            need=need,
            safety=safety,
            selection=selection,
        )
    )

    assert (
        recommendation.status
        == "ready_to_schedule"
    )

    assert recommendation.protocol is not None

    assert (
        recommendation.protocol.protocol_id
        == "half_cooper"
    )
