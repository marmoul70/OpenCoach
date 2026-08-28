from datetime import date
from uuid import UUID, uuid4

import pytest

from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    TrainingSession,
)
from opencoach.physiology.testing import (
    ApplyPhysiologicalTestDecisionService,
    PhysiologicalMetric,
    PhysiologicalTestApplicationError,
    PhysiologicalTestApplicationStatus,
    PhysiologicalTestProposal,
    PhysiologicalTestReplacementStimulus,
    PhysiologicalTestType,
)


TODAY = date(
    2026,
    8,
    28,
)


class FakeTrainingSessionRepository(
    TrainingSessionRepository
):
    def __init__(
        self,
        sessions: tuple[
            TrainingSession,
            ...,
        ],
    ) -> None:
        self.sessions = {
            session.id: session
            for session in sessions
            if session.id is not None
        }

        self.save_calls = 0

    def save_session(
        self,
        athlete_profile_id: UUID,
        session: TrainingSession,
    ) -> TrainingSession:
        del athlete_profile_id

        self.save_calls += 1

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


def create_training_session(
    *,
    status: str = "planned",
    activity_id: UUID | None = None,
    session_type: str = "vo2max",
    planning_key: str | None = None,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=TODAY,
        type=session_type,
        sport_type="Run",
        title="VO2max",
        description="10 x 400 m",
        duration_minutes=50,
        planning_key=planning_key,
        intensity="hard",
        status=status,
        activity_id=activity_id,
    )


def create_proposal(
    *,
    session_id: UUID | None,
) -> PhysiologicalTestProposal:
    return PhysiologicalTestProposal(
        athlete_profile_id=uuid4(),
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
    )


def service_for(
    session: TrainingSession,
):
    repository = (
        FakeTrainingSessionRepository(
            (
                session,
            )
        )
    )

    service = (
        ApplyPhysiologicalTestDecisionService(
            training_session_repository=(
                repository
            ),
        )
    )

    return (
        service,
        repository,
    )


def test_pending_proposal_does_not_modify_session() -> None:
    session = create_training_session()

    service, repository = (
        service_for(
            session
        )
    )

    result = service.apply(
        proposal=create_proposal(
            session_id=session.id,
        ),
    )

    assert (
        result.status
        is PhysiologicalTestApplicationStatus
        .AWAITING_ATHLETE
    )

    assert repository.save_calls == 0


def test_declined_test_keeps_original_session() -> None:
    session = create_training_session()

    service, repository = (
        service_for(
            session
        )
    )

    proposal = (
        create_proposal(
            session_id=session.id,
        )
        .decline()
    )

    result = service.apply(
        proposal=proposal,
    )

    assert (
        result.status
        is PhysiologicalTestApplicationStatus
        .DECLINED
    )

    assert repository.save_calls == 0

    assert (
        repository.sessions[
            session.id
        ].type
        == "vo2max"
    )


def test_accepted_test_replaces_same_session() -> None:
    session = create_training_session()

    service, repository = (
        service_for(
            session
        )
    )

    proposal = (
        create_proposal(
            session_id=session.id,
        )
        .accept()
    )

    result = service.apply(
        proposal=proposal,
    )

    assert (
        result.status
        is PhysiologicalTestApplicationStatus
        .APPLIED
    )

    assert result.changed is True

    assert repository.save_calls == 1

    replaced = (
        result.resulting_session
    )

    assert replaced is not None

    assert (
        replaced.id
        == session.id
    )

    assert (
        replaced.date
        == session.date
    )

    assert (
        replaced.type
        == "physiological_test"
    )

    assert (
        replaced.planning_key
        == "physiological_test:half_cooper"
    )


def test_accepted_half_cooper_uses_generated_session_content() -> None:
    session = create_training_session()

    service, _ = service_for(
        session
    )

    result = service.apply(
        proposal=(
            create_proposal(
                session_id=session.id,
            )
            .accept()
        ),
    )

    replaced = (
        result.resulting_session
    )

    assert replaced is not None

    assert (
        replaced.title
        == "Test VMA — Demi-Cooper 6 min"
    )

    assert (
        replaced.duration_minutes
        == 44
    )

    assert (
        "Demi-Cooper"
        in replaced.description
    )

    assert (
        "Échauffement"
        in replaced.description
    )


def test_test_never_creates_extra_session() -> None:
    session = create_training_session()

    service, repository = (
        service_for(
            session
        )
    )

    ids_before = set(
        repository.sessions
    )

    service.apply(
        proposal=(
            create_proposal(
                session_id=session.id,
            )
            .accept()
        ),
    )

    ids_after = set(
        repository.sessions
    )

    assert (
        ids_after
        == ids_before
    )


def test_accepted_proposal_requires_target_session() -> None:
    session = create_training_session()

    service, _ = service_for(
        session
    )

    proposal = (
        create_proposal(
            session_id=None,
        )
        .accept()
    )

    with pytest.raises(
        PhysiologicalTestApplicationError
    ):
        service.apply(
            proposal=proposal,
        )


def test_missing_target_session_is_rejected() -> None:
    session = create_training_session()

    service, _ = service_for(
        session
    )

    proposal = (
        create_proposal(
            session_id=uuid4(),
        )
        .accept()
    )

    with pytest.raises(
        PhysiologicalTestApplicationError
    ):
        service.apply(
            proposal=proposal,
        )


def test_completed_session_cannot_be_replaced() -> None:
    session = create_training_session(
        status="completed",
    )

    service, _ = service_for(
        session
    )

    with pytest.raises(
        PhysiologicalTestApplicationError
    ):
        service.apply(
            proposal=(
                create_proposal(
                    session_id=session.id,
                )
                .accept()
            ),
        )


def test_skipped_session_cannot_be_replaced() -> None:
    session = create_training_session(
        status="skipped",
    )

    service, _ = service_for(
        session
    )

    with pytest.raises(
        PhysiologicalTestApplicationError
    ):
        service.apply(
            proposal=(
                create_proposal(
                    session_id=session.id,
                )
                .accept()
            ),
        )


def test_session_with_activity_cannot_be_replaced() -> None:
    session = create_training_session(
        activity_id=uuid4(),
    )

    service, _ = service_for(
        session
    )

    with pytest.raises(
        PhysiologicalTestApplicationError
    ):
        service.apply(
            proposal=(
                create_proposal(
                    session_id=session.id,
                )
                .accept()
            ),
        )


def test_application_is_idempotent() -> None:
    session = create_training_session()

    service, repository = (
        service_for(
            session
        )
    )

    proposal = (
        create_proposal(
            session_id=session.id,
        )
        .accept()
    )

    first = service.apply(
        proposal=proposal,
    )

    assert (
        first.status
        is PhysiologicalTestApplicationStatus
        .APPLIED
    )

    second = service.apply(
        proposal=proposal,
    )

    assert (
        second.status
        is PhysiologicalTestApplicationStatus
        .ALREADY_APPLIED
    )

    assert repository.save_calls == 1
