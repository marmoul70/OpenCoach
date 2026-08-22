from opencoach.planning import (
    AssessmentNeed,
    AssessmentSelectionContext,
    select_assessment_protocol,
)


def create_need(
    assessment_type="vma_calibration",
) -> AssessmentNeed:
    if assessment_type == "threshold_calibration":
        metrics = (
            "threshold_heart_rate_1",
            "threshold_heart_rate_2",
        )

    elif assessment_type == "max_heart_rate_calibration":
        metrics = (
            "max_heart_rate",
        )

    else:
        metrics = (
            "vma",
        )

    return AssessmentNeed(
        assessment_type=assessment_type,
        priority="high",
        metrics=metrics,
        reason="Calibration nécessaire.",
    )


def test_vameval_is_preferred_when_track_is_available() -> None:
    selection = select_assessment_protocol(
        need=create_need(),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=True,
            flat_route_available=True,
        ),
    )

    assert selection.has_solution is True

    assert selection.best_candidate is not None

    assert (
        selection.best_candidate.protocol.protocol_id
        == "vameval"
    )


def test_half_cooper_is_selected_without_track() -> None:
    selection = select_assessment_protocol(
        need=create_need(),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=False,
            flat_route_available=True,
        ),
    )

    assert selection.has_solution is True

    assert selection.best_candidate is not None

    assert (
        selection.best_candidate.protocol.protocol_id
        == "half_cooper"
    )


def test_maximal_tests_can_be_blocked() -> None:
    selection = select_assessment_protocol(
        need=create_need(),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=False,
            track_available=True,
            flat_route_available=True,
        ),
    )

    assert selection.has_solution is False

    assert all(
        candidate.eligible is False
        for candidate in selection.candidates
    )


def test_track_protocol_is_rejected_without_track() -> None:
    selection = select_assessment_protocol(
        need=create_need(),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            track_available=False,
            flat_route_available=True,
        ),
    )

    vameval = next(
        candidate
        for candidate in selection.candidates
        if candidate.protocol.protocol_id
        == "vameval"
    )

    assert vameval.eligible is False

    assert any(
        "piste"
        in reason
        for reason in vameval.reasons
    )


def test_threshold_field_test_cannot_cover_both_thresholds() -> None:
    need = AssessmentNeed(
        assessment_type="threshold_calibration",
        priority="high",
        metrics=(
            "threshold_heart_rate_1",
            "threshold_heart_rate_2",
        ),
        reason="Calibration complète des seuils.",
    )

    selection = select_assessment_protocol(
        need=need,
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            flat_route_available=True,
            laboratory_available=False,
        ),
    )

    assert selection.has_solution is False

    twenty_minutes = next(
        candidate
        for candidate in selection.candidates
        if candidate.protocol.protocol_id
        == "twenty_minute_threshold"
    )

    assert twenty_minutes.eligible is False

def test_laboratory_threshold_is_available_when_lab_exists() -> None:
    selection = select_assessment_protocol(
        need=create_need(
            "threshold_calibration"
        ),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            flat_route_available=False,
            laboratory_available=True,
        ),
    )

    assert selection.best_candidate is not None

    assert (
        selection.best_candidate.protocol.protocol_id
        == "laboratory_threshold"
    )


def test_no_solution_when_required_environments_are_missing() -> None:
    selection = select_assessment_protocol(
        need=create_need(
            "threshold_calibration"
        ),
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            flat_route_available=False,
            laboratory_available=False,
        ),
    )

    assert selection.has_solution is False

def test_twenty_minute_test_can_cover_sv2_only() -> None:
    need = AssessmentNeed(
        assessment_type="threshold_calibration",
        priority="high",
        metrics=(
            "threshold_heart_rate_2",
        ),
        reason="SV2 à recalibrer.",
    )

    selection = select_assessment_protocol(
        need=need,
        context=AssessmentSelectionContext(
            maximal_testing_allowed=True,
            flat_route_available=True,
            laboratory_available=False,
        ),
    )

    assert selection.has_solution is True

    assert selection.best_candidate is not None

    assert (
        selection.best_candidate.protocol.protocol_id
        == "twenty_minute_threshold"
    )