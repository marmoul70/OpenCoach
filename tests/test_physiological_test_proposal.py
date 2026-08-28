from datetime import date
from uuid import uuid4

import pytest

from opencoach.physiology.testing import (
    PhysiologicalMetric,
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
    PhysiologicalTestProposalRequest,
    PhysiologicalTestType,
    PhysiologicalTestReplacementStimulus,
    propose_physiological_test,
)


TEST_DATE = date(
    2026,
    9,
    9,
)


def create_proposal() -> PhysiologicalTestProposal:
    return PhysiologicalTestProposal(
        athlete_profile_id=uuid4(),
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        target_metrics=(
            PhysiologicalMetric.VMA,
        ),
        proposed_date=TEST_DATE,
        reason=(
            "La dernière VMA disponible "
            "n'est plus suffisamment récente."
        ),
        recommendation=(
            "OpenCoach recommande un Demi-Cooper."
        ),
        replacement_stimulus=(
            PhysiologicalTestReplacementStimulus.AEROBIC_POWER
        ),
    )


def test_new_proposal_is_pending() -> None:
    proposal = create_proposal()

    assert (
        proposal.decision
        is PhysiologicalTestDecision.PENDING
    )

    assert (
        proposal.awaiting_athlete_decision
        is True
    )

    assert proposal.test_authorized is False


def test_athlete_can_accept_test() -> None:
    proposal = (
        create_proposal()
        .accept()
    )

    assert (
        proposal.decision
        is PhysiologicalTestDecision.ACCEPTED
    )

    assert proposal.test_authorized is True

    assert (
        proposal.replacement_required
        is False
    )


def test_athlete_can_decline_test() -> None:
    proposal = (
        create_proposal()
        .decline()
    )

    assert (
        proposal.decision
        is PhysiologicalTestDecision.DECLINED
    )

    assert proposal.test_authorized is False

    assert (
        proposal.replacement_required
        is True
    )


def test_declining_preserves_replacement_stimulus() -> None:
    proposal = (
        create_proposal()
        .decline()
    )

    assert (
        proposal.replacement_stimulus
        is PhysiologicalTestReplacementStimulus.AEROBIC_POWER
    )


def test_proposal_is_immutable() -> None:
    proposal = create_proposal()

    with pytest.raises(
        AttributeError
    ):
        proposal.reason = "Autre"


def test_service_builds_half_cooper_proposal() -> None:
    proposal = (
        propose_physiological_test(
            PhysiologicalTestProposalRequest(
                athlete_profile_id=uuid4(),
                protocol=(
                    PhysiologicalTestType.HALF_COOPER
                ),
                proposed_date=TEST_DATE,
                reason=(
                    "VMA vieillissante."
                ),
            )
        )
    )

    assert (
        proposal.protocol
        is PhysiologicalTestType.HALF_COOPER
    )

    assert (
        PhysiologicalMetric.VMA
        in proposal.target_metrics
    )

    assert (
        proposal.replacement_stimulus
        is PhysiologicalTestReplacementStimulus.AEROBIC_POWER
    )

    assert (
        "facultatif"
        in proposal.recommendation
    )


def test_threshold_test_decline_keeps_threshold_stimulus() -> None:
    proposal = (
        propose_physiological_test(
            PhysiologicalTestProposalRequest(
                athlete_profile_id=uuid4(),
                protocol=(
                    PhysiologicalTestType.THRESHOLD_30_MIN
                ),
                proposed_date=TEST_DATE,
                reason=(
                    "Seuil à recalibrer."
                ),
            )
        )
        .decline()
    )

    assert (
        proposal.replacement_stimulus
        is PhysiologicalTestReplacementStimulus.THRESHOLD
    )


def test_uphill_test_decline_keeps_uphill_quality() -> None:
    proposal = (
        propose_physiological_test(
            PhysiologicalTestProposalRequest(
                athlete_profile_id=uuid4(),
                protocol=(
                    PhysiologicalTestType.UPHILL_6_MIN
                ),
                proposed_date=TEST_DATE,
                reason=(
                    "Profil ascensionnel à actualiser."
                ),
            )
        )
        .decline()
    )

    assert (
        proposal.replacement_stimulus
        is PhysiologicalTestReplacementStimulus.UPHILL_INTENSITY
    )


def test_proposal_can_be_assigned_to_training_session() -> None:
    session_id = uuid4()

    assigned = (
        create_proposal()
        .assign_to_session(
            session_id
        )
    )

    assert (
        assigned.target_session_id
        == session_id
    )


def test_accept_preserves_target_session() -> None:
    session_id = uuid4()

    accepted = (
        create_proposal()
        .assign_to_session(
            session_id
        )
        .accept()
    )

    assert (
        accepted.target_session_id
        == session_id
    )


def test_decline_preserves_target_session() -> None:
    session_id = uuid4()

    declined = (
        create_proposal()
        .assign_to_session(
            session_id
        )
        .decline()
    )

    assert (
        declined.target_session_id
        == session_id
    )
