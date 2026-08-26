from uuid import uuid4

import pytest

from opencoach.coaching.daily_adaptation import (
    AdaptationDecision,
    CoachAdaptationProposal,
)


def create_proposal() -> CoachAdaptationProposal:
    return CoachAdaptationProposal(
        checkin_id=uuid4(),
        reason=(
            "Douleur déclarée lors du check-in."
        ),
        recommendation=(
            "Souhaites-tu adapter la séance prévue ?"
        ),
    )


def test_proposal_is_pending_by_default() -> None:
    proposal = create_proposal()

    assert (
        proposal.decision
        is AdaptationDecision.PENDING
    )

    assert proposal.awaiting_athlete_decision
    assert not proposal.adaptation_authorized


def test_athlete_can_accept_adaptation() -> None:
    proposal = create_proposal()

    accepted = proposal.accept()

    assert (
        accepted.decision
        is AdaptationDecision.ACCEPTED
    )

    assert not accepted.awaiting_athlete_decision
    assert accepted.adaptation_authorized

    assert proposal.awaiting_athlete_decision


def test_athlete_can_decline_adaptation() -> None:
    proposal = create_proposal()

    declined = proposal.decline()

    assert (
        declined.decision
        is AdaptationDecision.DECLINED
    )

    assert not declined.awaiting_athlete_decision
    assert not declined.adaptation_authorized


def test_proposal_requires_reason() -> None:
    with pytest.raises(
        ValueError,
        match="raison",
    ):
        CoachAdaptationProposal(
            checkin_id=uuid4(),
            reason=" ",
            recommendation=(
                "Souhaites-tu adapter la séance ?"
            ),
        )


def test_proposal_requires_recommendation() -> None:
    with pytest.raises(
        ValueError,
        match="recommandation",
    ):
        CoachAdaptationProposal(
            checkin_id=uuid4(),
            reason="Fatigue importante.",
            recommendation=" ",
        )
