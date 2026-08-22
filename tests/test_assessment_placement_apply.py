from datetime import date

import pytest

from opencoach.planning import (
    AssessmentPlacementApplyError,
    AssessmentPlacementProposal,
    AssessmentSessionSpec,
    apply_assessment_placement,
)


TARGET_DATE = date(
    2026,
    8,
    26,
)

THURSDAY = date(
    2026,
    8,
    27,
)


def create_spec() -> AssessmentSessionSpec:
    return AssessmentSessionSpec(
        assessment_type="vma_calibration",
        protocol_id="vameval",
        title="Test VAMEVAL",
        description="Calibration de la VMA.",
        sport_type="run",
        intensity="maximal",
        duration_minutes=45,
        priority="high",
        requires_maximal_effort=True,
        covered_metrics=(
            "vma",
            "max_heart_rate",
        ),
    )


def test_direct_proposal_can_be_applied() -> None:
    proposal = AssessmentPlacementProposal(
        status="proposed",
        spec=create_spec(),
        target_date=TARGET_DATE,
        proposed_date=TARGET_DATE,
        requires_confirmation=False,
        reasons=(),
        rejected_reasons=(),
    )

    application = apply_assessment_placement(
        proposal=proposal
    )

    assert (
        application.session.date
        == TARGET_DATE
    )

    assert (
        application.session.type
        == "assessment"
    )

    assert (
        application.session.intensity
        == "very_hard"
    )

    assert (
        application.athlete_confirmation_used
        is False
    )


def test_confirmation_required_proposal_is_rejected_without_confirmation() -> None:
    proposal = AssessmentPlacementProposal(
        status="confirmation_required",
        spec=create_spec(),
        target_date=TARGET_DATE,
        proposed_date=THURSDAY,
        requires_confirmation=True,
        reasons=(),
        rejected_reasons=(),
    )

    with pytest.raises(
        AssessmentPlacementApplyError,
        match="confirmation",
    ):
        apply_assessment_placement(
            proposal=proposal,
            confirmed=False,
        )


def test_confirmation_required_proposal_can_be_applied_after_confirmation() -> None:
    proposal = AssessmentPlacementProposal(
        status="confirmation_required",
        spec=create_spec(),
        target_date=TARGET_DATE,
        proposed_date=THURSDAY,
        requires_confirmation=True,
        reasons=(),
        rejected_reasons=(),
    )

    application = apply_assessment_placement(
        proposal=proposal,
        confirmed=True,
    )

    assert (
        application.session.date
        == THURSDAY
    )

    assert (
        application.athlete_confirmation_used
        is True
    )


def test_no_solution_cannot_be_applied() -> None:
    proposal = AssessmentPlacementProposal(
        status="no_solution",
        spec=create_spec(),
        target_date=TARGET_DATE,
        proposed_date=None,
        requires_confirmation=False,
        reasons=(),
        rejected_reasons=(),
    )

    with pytest.raises(
        AssessmentPlacementApplyError,
        match="sans solution",
    ):
        apply_assessment_placement(
            proposal=proposal
        )


def test_confirmation_flag_does_not_change_direct_proposal() -> None:
    proposal = AssessmentPlacementProposal(
        status="proposed",
        spec=create_spec(),
        target_date=TARGET_DATE,
        proposed_date=TARGET_DATE,
        requires_confirmation=False,
        reasons=(),
        rejected_reasons=(),
    )

    application = apply_assessment_placement(
        proposal=proposal,
        confirmed=True,
    )

    assert (
        application.athlete_confirmation_used
        is False
    )
