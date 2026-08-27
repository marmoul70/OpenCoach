from datetime import date
from uuid import uuid4

import pytest

from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)
from opencoach.coaching.daily_adaptation_application import (
    ApplyAcceptedDailyAdaptationService,
    DailyAdaptationApplicationError,
    DailyAdaptationSessionAmbiguousError,
    DailyAdaptationSessionNotFoundError,
)
from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
)
from opencoach.models import (
    TrainingSession,
)


TODAY = date(
    2026,
    8,
    26,
)


class FakeTrainingSessionRepository:
    def __init__(
        self,
        sessions=(),
    ):
        self.sessions = list(
            sessions
        )

        self.saved = []

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        del athlete_profile_id

        return [
            session
            for session in self.sessions
            if (
                start_date
                <= session.date
                <= end_date
            )
        ]

    def save_session(
        self,
        athlete_profile_id,
        session,
    ):
        del athlete_profile_id

        self.saved.append(
            session
        )

        return session


def _checkin(
    *,
    energy=5,
    pain=3,
    unavailable=False,
):
    return AthleteDailyCheckIn(
        id=uuid4(),
        date=TODAY,
        energy_rating=energy,
        pain_wellness_rating=pain,
        unavailable=unavailable,
    )


def _proposal(
    checkin,
    *,
    accepted=True,
):
    proposal = CoachAdaptationProposal(
        id=uuid4(),
        checkin_id=checkin.id,
        reason="Douleur modérée.",
        recommendation="Adapter la séance ?",
    )

    return (
        proposal.accept()
        if accepted
        else proposal.decline()
    )


def _session(
    *,
    slot="threshold",
):
    return TrainingSession(
        id=uuid4(),
        date=TODAY,
        type="threshold",
        sport_type="Run",
        title="Travail au seuil",
        description="Séance qualitative.",
        duration_minutes=60,
        intensity="hard",
        status="planned",
        planning_key=(
            f"2026-08-24:{slot}"
        ),
    )


def test_accepted_proposal_adapts_unique_session() -> None:
    checkin = _checkin()

    repository = (
        FakeTrainingSessionRepository(
            (
                _session(),
            )
        )
    )

    service = (
        ApplyAcceptedDailyAdaptationService(
            training_session_repository=(
                repository
            )
        )
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        checkin=checkin,
        proposal=_proposal(
            checkin
        ),
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

    assert len(
        repository.saved
    ) == 1


def test_declined_proposal_is_never_applied() -> None:
    checkin = _checkin()

    repository = (
        FakeTrainingSessionRepository(
            (
                _session(),
            )
        )
    )

    service = (
        ApplyAcceptedDailyAdaptationService(
            training_session_repository=repository
        )
    )

    with pytest.raises(
        DailyAdaptationApplicationError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            checkin=checkin,
            proposal=_proposal(
                checkin,
                accepted=False,
            ),
        )

    assert repository.saved == []


def test_missing_session_is_reported() -> None:
    checkin = _checkin()

    service = (
        ApplyAcceptedDailyAdaptationService(
            training_session_repository=(
                FakeTrainingSessionRepository()
            )
        )
    )

    with pytest.raises(
        DailyAdaptationSessionNotFoundError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            checkin=checkin,
            proposal=_proposal(
                checkin
            ),
        )


def test_multiple_sessions_are_never_chosen_arbitrarily() -> None:
    checkin = _checkin()

    repository = (
        FakeTrainingSessionRepository(
            (
                _session(
                    slot="running",
                ),
                _session(
                    slot="strength",
                ),
            )
        )
    )

    service = (
        ApplyAcceptedDailyAdaptationService(
            training_session_repository=repository
        )
    )

    with pytest.raises(
        DailyAdaptationSessionAmbiguousError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            checkin=checkin,
            proposal=_proposal(
                checkin
            ),
        )

    assert repository.saved == []


def test_completed_session_is_not_candidate() -> None:
    checkin = _checkin()

    session = _session()
    session.status = "completed"

    service = (
        ApplyAcceptedDailyAdaptationService(
            training_session_repository=(
                FakeTrainingSessionRepository(
                    (
                        session,
                    )
                )
            )
        )
    )

    with pytest.raises(
        DailyAdaptationSessionNotFoundError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            checkin=checkin,
            proposal=_proposal(
                checkin
            ),
        )


def test_proposal_must_match_checkin() -> None:
    checkin = _checkin()

    proposal = CoachAdaptationProposal(
        id=uuid4(),
        checkin_id=uuid4(),
        reason="Douleur.",
        recommendation="Adapter ?",
    ).accept()

    service = (
        ApplyAcceptedDailyAdaptationService(
            training_session_repository=(
                FakeTrainingSessionRepository(
                    (
                        _session(),
                    )
                )
            )
        )
    )

    with pytest.raises(
        DailyAdaptationApplicationError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            checkin=checkin,
            proposal=proposal,
        )


def test_unavailable_session_is_persisted_as_skipped() -> None:
    checkin = _checkin(
        pain=5,
        unavailable=True,
    )

    repository = FakeTrainingSessionRepository(
        (
            _session(),
        )
    )

    service = ApplyAcceptedDailyAdaptationService(
        training_session_repository=repository,
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        checkin=checkin,
        proposal=_proposal(
            checkin,
        ),
    )

    assert result.changed

    assert (
        result.adapted.status
        == "skipped"
    )

    assert len(
        repository.saved
    ) == 1

    assert (
        repository.saved[0].status
        == "skipped"
    )
