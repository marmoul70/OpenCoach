from datetime import date
from uuid import uuid4

import pytest

from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)
from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
    BodySide,
    PainArea,
    PainLocation,
)
from opencoach.coaching.daily_session_adaptation import (
    DailySessionAdaptationError,
    adapt_daily_training_session,
)
from opencoach.models import (
    TrainingSession,
)


TODAY = date(
    2026,
    8,
    26,
)


def _session(
    *,
    intensity="hard",
    duration=60,
    status="planned",
):
    return TrainingSession(
        id=uuid4(),
        date=TODAY,
        type="threshold",
        sport_type="Run",
        title="Travail au seuil",
        description="Séance qualitative.",
        duration_minutes=duration,
        intensity=intensity,
        status=status,
        planning_key=(
            "2026-08-24:threshold"
        ),
    )


def _checkin(
    *,
    energy=5,
    pain=5,
    illness=False,
    locations=(),
):
    return AthleteDailyCheckIn(
        id=uuid4(),
        date=TODAY,
        energy_rating=energy,
        pain_wellness_rating=pain,
        illness=illness,
        pain_locations=locations,
    )


def _proposal(
    *,
    accepted=True,
):
    proposal = CoachAdaptationProposal(
        id=uuid4(),
        checkin_id=uuid4(),
        reason="Check-in à surveiller.",
        recommendation="Adapter la séance ?",
    )

    return (
        proposal.accept()
        if accepted
        else proposal.decline()
    )


def test_declined_proposal_cannot_modify_session() -> None:
    with pytest.raises(
        DailySessionAdaptationError
    ):
        adapt_daily_training_session(
            session=_session(),
            checkin=_checkin(
                pain=3,
            ),
            proposal=_proposal(
                accepted=False,
            ),
        )


def test_completed_session_cannot_be_modified() -> None:
    with pytest.raises(
        DailySessionAdaptationError
    ):
        adapt_daily_training_session(
            session=_session(
                status="completed",
            ),
            checkin=_checkin(
                pain=3,
            ),
            proposal=_proposal(),
        )


def test_three_hearts_replaces_hard_session_with_easy() -> None:
    result = adapt_daily_training_session(
        session=_session(
            intensity="hard",
            duration=60,
        ),
        checkin=_checkin(
            pain=3,
            locations=(
                PainLocation(
                    area=PainArea.LOWER_BACK,
                    side=BodySide.CENTER,
                ),
            ),
        ),
        proposal=_proposal(),
    )

    assert result.changed

    assert (
        result.adapted.type
        == "aerobic_easy"
    )

    assert (
        result.adapted.intensity
        == "easy"
    )

    assert (
        result.adapted.duration_minutes
        == 45
    )


def test_three_stars_reduces_easy_session_duration() -> None:
    result = adapt_daily_training_session(
        session=_session(
            intensity="easy",
            duration=50,
        ),
        checkin=_checkin(
            energy=3,
        ),
        proposal=_proposal(),
    )

    assert result.changed

    assert (
        result.adapted.duration_minutes
        == 40
    )

    assert (
        result.adapted.intensity
        == "easy"
    )


def test_two_hearts_creates_short_recovery_session() -> None:
    result = adapt_daily_training_session(
        session=_session(
            duration=75,
        ),
        checkin=_checkin(
            pain=2,
        ),
        proposal=_proposal(),
    )

    assert result.changed

    assert (
        result.adapted.type
        == "recovery"
    )

    assert (
        result.adapted.duration_minutes
        == 30
    )

    assert (
        result.adapted.intensity
        == "easy"
    )


def test_illness_creates_short_recovery_session() -> None:
    result = adapt_daily_training_session(
        session=_session(
            duration=60,
        ),
        checkin=_checkin(
            illness=True,
        ),
        proposal=_proposal(),
    )

    assert (
        result.adapted.type
        == "recovery"
    )

    assert (
        result.adapted.duration_minutes
        == 30
    )


def test_good_checkin_does_not_change_session() -> None:
    session = _session(
        intensity="easy",
        duration=45,
    )

    result = adapt_daily_training_session(
        session=session,
        checkin=_checkin(),
        proposal=_proposal(),
    )

    assert not result.changed

    assert (
        result.adapted
        == session
    )


def test_adaptation_preserves_session_identity() -> None:
    session = _session()

    result = adapt_daily_training_session(
        session=session,
        checkin=_checkin(
            pain=3,
        ),
        proposal=_proposal(),
    )

    assert (
        result.adapted.id
        == session.id
    )

    assert (
        result.adapted.planning_key
        == session.planning_key
    )

    assert (
        result.adapted.date
        == session.date
    )
