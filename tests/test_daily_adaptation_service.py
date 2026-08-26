from datetime import date
from uuid import uuid4

from opencoach.coaching.daily_adaptation import (
    AdaptationDecision,
)
from opencoach.coaching.daily_adaptation_service import (
    build_daily_adaptation_proposal,
)
from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
    BodySide,
    PainArea,
    PainLocation,
)
from opencoach.coaching.daily_checkin_policy import (
    CheckInCoachAction,
    assess_daily_checkin,
)


TODAY = date(
    2026,
    8,
    26,
)


def _checkin(
    *,
    energy=5,
    pain=5,
    illness=False,
    unavailable=False,
    locations=(),
):
    return AthleteDailyCheckIn(
        date=TODAY,
        energy_rating=energy,
        pain_wellness_rating=pain,
        illness=illness,
        unavailable=unavailable,
        pain_locations=locations,
    )


def test_normal_checkin_creates_no_proposal() -> None:
    assessment = assess_daily_checkin(
        _checkin()
    )

    proposal = build_daily_adaptation_proposal(
        checkin_id=uuid4(),
        assessment=assessment,
    )

    assert proposal is None


def test_light_discomfort_is_monitored_without_proposal() -> None:
    assessment = assess_daily_checkin(
        _checkin(
            pain=4,
        )
    )

    assert (
        assessment.action
        is CheckInCoachAction.MONITOR
    )

    proposal = build_daily_adaptation_proposal(
        checkin_id=uuid4(),
        assessment=assessment,
    )

    assert proposal is None


def test_three_hearts_creates_pending_adaptation_proposal() -> None:
    checkin_id = uuid4()

    assessment = assess_daily_checkin(
        _checkin(
            pain=3,
            locations=(
                PainLocation(
                    area=PainArea.LOWER_BACK,
                    side=BodySide.CENTER,
                ),
            ),
        )
    )

    proposal = build_daily_adaptation_proposal(
        checkin_id=checkin_id,
        assessment=assessment,
    )

    assert proposal is not None

    assert (
        proposal.checkin_id
        == checkin_id
    )

    assert (
        proposal.decision
        is AdaptationDecision.PENDING
    )

    assert (
        "lower_back:center"
        in proposal.reason
    )

    assert (
        "Veux-tu adapter"
        in proposal.recommendation
    )


def test_severe_pain_creates_strong_recommendation() -> None:
    assessment = assess_daily_checkin(
        _checkin(
            pain=2,
        )
    )

    proposal = build_daily_adaptation_proposal(
        checkin_id=uuid4(),
        assessment=assessment,
    )

    assert proposal is not None

    assert (
        "fortement recommandée"
        in proposal.recommendation
    )


def test_illness_creates_strong_recommendation() -> None:
    assessment = assess_daily_checkin(
        _checkin(
            illness=True,
        )
    )

    proposal = build_daily_adaptation_proposal(
        checkin_id=uuid4(),
        assessment=assessment,
    )

    assert proposal is not None

    assert (
        "Maladie déclarée."
        in proposal.reason
    )


def test_proposal_acceptance_is_explicit() -> None:
    assessment = assess_daily_checkin(
        _checkin(
            energy=3,
        )
    )

    proposal = build_daily_adaptation_proposal(
        checkin_id=uuid4(),
        assessment=assessment,
    )

    assert proposal is not None
    assert not proposal.adaptation_authorized

    accepted = proposal.accept()

    assert accepted.adaptation_authorized


def test_proposal_refusal_preserves_decision() -> None:
    assessment = assess_daily_checkin(
        _checkin(
            pain=3,
        )
    )

    proposal = build_daily_adaptation_proposal(
        checkin_id=uuid4(),
        assessment=assessment,
    )

    assert proposal is not None

    declined = proposal.decline()

    assert (
        declined.decision
        is AdaptationDecision.DECLINED
    )

    assert not declined.adaptation_authorized
