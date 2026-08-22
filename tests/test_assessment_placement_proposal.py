from datetime import date

from opencoach.planning import (
    AssessmentSessionSpec,
    PlacementRuleResult,
    SessionPlacementCandidate,
    SessionPlacementResult,
    build_assessment_placement_proposal,
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
        description="Calibration VMA.",
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


def create_candidate(
    *,
    candidate_date: date,
    eligible: bool = True,
    preferred: bool = True,
    requires_confirmation: bool = False,
    reasons=(),
    rules=(),
) -> SessionPlacementCandidate:
    return SessionPlacementCandidate(
        date=candidate_date,
        calendar_score=100,
        placement_score=100,
        eligible=eligible,
        preferred=preferred,
        requires_confirmation=(
            requires_confirmation
        ),
        running_allowed=True,
        cross_training_allowed=True,
        max_duration_minutes=None,
        rules=tuple(rules),
        reasons=tuple(reasons),
    )


def test_target_date_can_be_proposed_directly() -> None:
    candidate = create_candidate(
        candidate_date=TARGET_DATE,
        preferred=True,
    )

    proposal = (
        build_assessment_placement_proposal(
            spec=create_spec(),
            target_date=TARGET_DATE,
            placement=SessionPlacementResult(
                eligible_candidates=(
                    candidate,
                ),
                rejected_candidates=(),
            ),
        )
    )

    assert proposal.status == "proposed"

    assert (
        proposal.proposed_date
        == TARGET_DATE
    )

    assert (
        proposal.requires_confirmation
        is False
    )

    assert (
        proposal.can_be_applied_directly
        is True
    )


def test_alternative_day_can_require_confirmation() -> None:
    candidate = create_candidate(
        candidate_date=THURSDAY,
        preferred=False,
        requires_confirmation=True,
        reasons=(
            "Jour non habituel à confirmer avec l'athlète.",
        ),
    )

    proposal = (
        build_assessment_placement_proposal(
            spec=create_spec(),
            target_date=TARGET_DATE,
            placement=SessionPlacementResult(
                eligible_candidates=(
                    candidate,
                ),
                rejected_candidates=(),
            ),
        )
    )

    assert (
        proposal.status
        == "confirmation_required"
    )

    assert (
        proposal.proposed_date
        == THURSDAY
    )

    assert (
        proposal.requires_confirmation
        is True
    )

    assert (
        proposal.can_be_applied_directly
        is False
    )


def test_no_solution_is_explicit() -> None:
    proposal = (
        build_assessment_placement_proposal(
            spec=create_spec(),
            target_date=TARGET_DATE,
            placement=SessionPlacementResult(
                eligible_candidates=(),
                rejected_candidates=(),
            ),
        )
    )

    assert (
        proposal.status
        == "no_solution"
    )

    assert proposal.proposed_date is None
    assert proposal.has_solution is False


def test_rejected_rule_reasons_are_preserved() -> None:
    rule = PlacementRuleResult(
        rule_id="hard_session_previous_day",
        severity="hard",
        violated=True,
        score_adjustment=0,
        reason=(
            "Séance intense déjà prévue la veille."
        ),
    )

    rejected = create_candidate(
        candidate_date=TARGET_DATE,
        eligible=False,
        rules=(
            rule,
        ),
    )

    alternative = create_candidate(
        candidate_date=THURSDAY,
        eligible=True,
        preferred=False,
        requires_confirmation=True,
    )

    proposal = (
        build_assessment_placement_proposal(
            spec=create_spec(),
            target_date=TARGET_DATE,
            placement=SessionPlacementResult(
                eligible_candidates=(
                    alternative,
                ),
                rejected_candidates=(
                    rejected,
                ),
            ),
        )
    )

    assert (
        "Séance intense déjà prévue la veille."
        in proposal.rejected_reasons
    )


def test_duplicate_rejection_reasons_are_not_repeated() -> None:
    rule = PlacementRuleResult(
        rule_id="duration_limit",
        severity="hard",
        violated=True,
        score_adjustment=0,
        reason=(
            "Durée prévue supérieure à la disponibilité du jour."
        ),
    )

    first = create_candidate(
        candidate_date=TARGET_DATE,
        eligible=False,
        rules=(rule,),
    )

    second = create_candidate(
        candidate_date=THURSDAY,
        eligible=False,
        rules=(rule,),
    )

    proposal = (
        build_assessment_placement_proposal(
            spec=create_spec(),
            target_date=TARGET_DATE,
            placement=SessionPlacementResult(
                eligible_candidates=(),
                rejected_candidates=(
                    first,
                    second,
                ),
            ),
        )
    )

    assert proposal.rejected_reasons == (
        "Durée prévue supérieure à la disponibilité du jour.",
    )
