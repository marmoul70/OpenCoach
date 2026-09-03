from __future__ import annotations

from dataclasses import replace
from datetime import date
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from opencoach.api.coaching.dependencies import (
    get_physiological_test_application_service,
    get_physiological_test_proposal_repository,
)
from opencoach.api.coaching.physiological_tests import (
    router,
)
from opencoach.api.intervals import (
    get_current_athlete_profile_id,
)
from opencoach.database.repositories.physiological_test_proposal import (
    PhysiologicalTestProposalRepository,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import TrainingSession
from opencoach.physiology.testing import (
    ApplyPhysiologicalTestDecisionService,
    PhysiologicalMetric,
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
    PhysiologicalTestReplacementStimulus,
    PhysiologicalTestType,
)


TODAY = date(
    2026,
    8,
    28,
)

ATHLETE_ID = uuid4()


class FakeProposalRepository(
    PhysiologicalTestProposalRepository
):
    def __init__(
        self,
        proposals: tuple[
            PhysiologicalTestProposal,
            ...,
        ] = (),
    ) -> None:
        self.proposals = {
            proposal.id: proposal
            for proposal in proposals
            if proposal.id is not None
        }

    def save(
        self,
        proposal: PhysiologicalTestProposal,
    ) -> PhysiologicalTestProposal:
        saved = proposal

        if saved.id is None:
            saved = replace(
                saved,
                id=uuid4(),
            )

        self.proposals[
            saved.id
        ] = saved

        return saved

    def get(
        self,
        athlete_profile_id: UUID,
        proposal_id: UUID,
    ) -> PhysiologicalTestProposal | None:
        proposal = self.proposals.get(
            proposal_id
        )

        if proposal is None:
            return None

        if (
            proposal.athlete_profile_id
            != athlete_profile_id
        ):
            return None

        return proposal

    def get_pending(
        self,
        athlete_profile_id: UUID,
    ) -> tuple[
        PhysiologicalTestProposal,
        ...,
    ]:
        return tuple(
            proposal
            for proposal
            in self.proposals.values()
            if (
                proposal.athlete_profile_id
                == athlete_profile_id
                and proposal.decision
                is PhysiologicalTestDecision.PENDING
            )
        )

    def list_since(
        self,
        athlete_profile_id: UUID,
        since: date,
    ) -> tuple[
        PhysiologicalTestProposal,
        ...,
    ]:
        return tuple(
            proposal
            for proposal
            in self.proposals.values()
            if (
                proposal.athlete_profile_id
                == athlete_profile_id
                and proposal.proposed_date
                >= since
            )
        )


class FakeTrainingSessionRepository(
    TrainingSessionRepository
):
    def __init__(
        self,
        sessions: tuple[
            TrainingSession,
            ...,
        ] = (),
    ) -> None:
        self.sessions = {
            session.id: session
            for session in sessions
            if session.id is not None
        }

    def save_session(
        self,
        athlete_profile_id: UUID,
        session: TrainingSession,
    ) -> TrainingSession:
        del athlete_profile_id

        assert session.id is not None

        self.sessions[
            session.id
        ] = session

        return session

    def get_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> TrainingSession | None:
        del athlete_profile_id

        return self.sessions.get(
            session_id
        )

    def delete_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> None:
        del athlete_profile_id

        self.sessions.pop(
            session_id,
            None,
        )

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TrainingSession]:
        del (
            athlete_profile_id,
            start_date,
            end_date,
        )

        return list(
            self.sessions.values()
        )

    def update_status(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        status: str,
    ) -> TrainingSession:
        del athlete_profile_id

        session = self.sessions[
            session_id
        ]

        updated = TrainingSession(
            **{
                **session.__dict__,
                "status": status,
            }
        )

        self.sessions[
            session_id
        ] = updated

        return updated

    def link_activity(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        activity_id: UUID | None,
    ) -> TrainingSession:
        del athlete_profile_id

        session = self.sessions[
            session_id
        ]

        updated = TrainingSession(
            **{
                **session.__dict__,
                "activity_id": activity_id,
            }
        )

        self.sessions[
            session_id
        ] = updated

        return updated

    def list_candidate_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ):
        del (
            athlete_profile_id,
            session_date,
        )

        return []

    def list_unlinked_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ):
        del (
            athlete_profile_id,
            session_date,
        )

        return []


def create_training_session() -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=TODAY,
        type="vo2max",
        sport_type="Run",
        title="VO2max",
        description="10 x 400 m",
        duration_minutes=50,
        intensity="hard",
        status="planned",
    )


def create_proposal(
    *,
    session_id: UUID | None,
    athlete_profile_id: UUID = ATHLETE_ID,
    decision: PhysiologicalTestDecision = (
        PhysiologicalTestDecision.PENDING
    ),
) -> PhysiologicalTestProposal:
    return PhysiologicalTestProposal(
        id=uuid4(),
        athlete_profile_id=(
            athlete_profile_id
        ),
        target_session_id=session_id,
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        target_metrics=(
            PhysiologicalMetric.VMA,
        ),
        proposed_date=TODAY,
        reason="VMA à recalibrer.",
        recommendation=(
            "OpenCoach recommande "
            "un Demi-Cooper."
        ),
        replacement_stimulus=(
            PhysiologicalTestReplacementStimulus
            .AEROBIC_POWER
        ),
        decision=decision,
    )


def create_client(
    *,
    proposals: tuple[
        PhysiologicalTestProposal,
        ...,
    ] = (),
    sessions: tuple[
        TrainingSession,
        ...,
    ] = (),
) -> tuple[
    TestClient,
    FakeProposalRepository,
    FakeTrainingSessionRepository,
]:
    proposal_repository = (
        FakeProposalRepository(
            proposals
        )
    )

    training_repository = (
        FakeTrainingSessionRepository(
            sessions
        )
    )

    application_service = (
        ApplyPhysiologicalTestDecisionService(
            training_session_repository=(
                training_repository
            ),
        )
    )

    app = FastAPI()

    app.include_router(
        router
    )

    app.dependency_overrides[
        get_current_athlete_profile_id
    ] = lambda: ATHLETE_ID

    app.dependency_overrides[
        get_physiological_test_proposal_repository
    ] = lambda: proposal_repository

    app.dependency_overrides[
        get_physiological_test_application_service
    ] = lambda: application_service

    return (
        TestClient(app),
        proposal_repository,
        training_repository,
    )


def test_pending_returns_empty_list() -> None:
    client, _, _ = create_client()

    response = client.get(
        "/api/coach/physiological-tests/pending"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_pending_returns_pending_proposal() -> None:
    session = create_training_session()

    proposal = create_proposal(
        session_id=session.id,
    )

    client, _, _ = create_client(
        proposals=(
            proposal,
        ),
        sessions=(
            session,
        ),
    )

    response = client.get(
        "/api/coach/physiological-tests/pending"
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1

    assert (
        payload[0]["id"]
        == str(proposal.id)
    )

    assert (
        payload[0]["protocol"]
        == "half_cooper"
    )

    assert (
        payload[0]["target_metrics"]
        == ["vma"]
    )

    assert (
        payload[0]["decision"]
        == "pending"
    )


def test_pending_excludes_other_athlete() -> None:
    session = create_training_session()

    proposal = create_proposal(
        session_id=session.id,
        athlete_profile_id=uuid4(),
    )

    client, _, _ = create_client(
        proposals=(
            proposal,
        ),
        sessions=(
            session,
        ),
    )

    response = client.get(
        "/api/coach/physiological-tests/pending"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_unknown_proposal_returns_404() -> None:
    client, _, _ = create_client()

    response = client.post(
        (
            "/api/coach/physiological-tests/"
            f"{uuid4()}/accept"
        )
    )

    assert response.status_code == 404


def test_accept_replaces_target_session_with_test() -> None:
    session = create_training_session()

    proposal = create_proposal(
        session_id=session.id,
    )

    client, proposals, training = (
        create_client(
            proposals=(
                proposal,
            ),
            sessions=(
                session,
            ),
        )
    )

    response = client.post(
        (
            "/api/coach/physiological-tests/"
            f"{proposal.id}/accept"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["proposal"]["decision"]
        == "accepted"
    )

    assert (
        payload["application_status"]
        == "applied"
    )

    assert (
        payload["changed"]
        is True
    )

    assert (
        payload["session"]
        is not None
    )

    assert (
        payload["session"]["id"]
        == str(session.id)
    )

    assert (
        payload["session"]["type"]
        == "physiological_test"
    )

    persisted_proposal = (
        proposals.get(
            ATHLETE_ID,
            proposal.id,
        )
    )

    assert persisted_proposal is not None

    assert (
        persisted_proposal.decision
        is PhysiologicalTestDecision.ACCEPTED
    )

    persisted_session = (
        training.sessions[
            session.id
        ]
    )

    assert (
        persisted_session.type
        == "physiological_test"
    )


def test_decline_keeps_original_quality_session() -> None:
    session = create_training_session()

    proposal = create_proposal(
        session_id=session.id,
    )

    client, proposals, training = (
        create_client(
            proposals=(
                proposal,
            ),
            sessions=(
                session,
            ),
        )
    )

    response = client.post(
        (
            "/api/coach/physiological-tests/"
            f"{proposal.id}/decline"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["proposal"]["decision"]
        == "declined"
    )

    assert (
        payload["application_status"]
        == "declined"
    )

    assert (
        payload["changed"]
        is False
    )

    assert (
        payload["session"]
        is None
    )

    persisted_proposal = (
        proposals.get(
            ATHLETE_ID,
            proposal.id,
        )
    )

    assert persisted_proposal is not None

    assert (
        persisted_proposal.decision
        is PhysiologicalTestDecision.DECLINED
    )

    persisted_session = (
        training.sessions[
            session.id
        ]
    )

    assert (
        persisted_session.type
        == "vo2max"
    )

    assert (
        persisted_session.title
        == "VO2max"
    )


def test_declined_proposal_cannot_be_accepted() -> None:
    session = create_training_session()

    proposal = create_proposal(
        session_id=session.id,
        decision=(
            PhysiologicalTestDecision.DECLINED
        ),
    )

    client, _, _ = create_client(
        proposals=(
            proposal,
        ),
        sessions=(
            session,
        ),
    )

    response = client.post(
        (
            "/api/coach/physiological-tests/"
            f"{proposal.id}/accept"
        )
    )

    assert response.status_code == 409


def test_accepted_proposal_cannot_be_declined() -> None:
    session = create_training_session()

    proposal = create_proposal(
        session_id=session.id,
        decision=(
            PhysiologicalTestDecision.ACCEPTED
        ),
    )

    client, _, _ = create_client(
        proposals=(
            proposal,
        ),
        sessions=(
            session,
        ),
    )

    response = client.post(
        (
            "/api/coach/physiological-tests/"
            f"{proposal.id}/decline"
        )
    )

    assert response.status_code == 409
