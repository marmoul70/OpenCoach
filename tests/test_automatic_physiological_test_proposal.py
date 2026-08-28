from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID, uuid4

from opencoach.models import (
    PhysiologicalMeasurement,
    TrainingSession,
)
from opencoach.physiology.testing.automatic_proposal import (
    AutomaticPhysiologicalTestProposalRequest,
    AutomaticPhysiologicalTestProposalService,
)

from opencoach.physiology.testing import (
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
    PhysiologicalTestReplacementStimulus,
    PhysiologicalTestType,
    SportDiscipline,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


TODAY = date(
    2026,
    8,
    28,
)

WEEK_START = date(
    2026,
    8,
    24,
)

WEEK_END = date(
    2026,
    8,
    30,
)

ATHLETE_ID = uuid4()


class FakeMeasurementRepository:
    def __init__(
        self,
        measurement=None,
    ):
        self.measurement = measurement

    def get_latest_measurement(
        self,
        athlete_profile_id,
        metric,
    ):
        del (
            athlete_profile_id,
            metric,
        )

        return self.measurement


class FakeProposalRepository:
    def __init__(
        self,
        proposals=(),
    ):
        self.values = list(
            proposals
        )

    def get_pending(
        self,
        athlete_profile_id,
    ):
        return tuple(
            proposal
            for proposal in self.values
            if (
                proposal.athlete_profile_id
                == athlete_profile_id
                and proposal.decision
                is PhysiologicalTestDecision.PENDING
            )
        )

    def list_since(
        self,
        athlete_profile_id,
        since,
    ):
        return tuple(
            proposal
            for proposal in self.values
            if (
                proposal.athlete_profile_id
                == athlete_profile_id
                and proposal.proposed_date
                >= since
            )
        )

    def save(
        self,
        proposal,
    ):
        if proposal.id is None:
            from dataclasses import replace

            proposal = replace(
                proposal,
                id=uuid4(),
            )

        self.values.append(
            proposal
        )

        return proposal


class FakeTrainingRepository:
    def __init__(
        self,
        sessions=(),
    ):
        self.sessions = list(
            sessions
        )

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


def session(
    session_type: str,
    *,
    session_date=date(
        2026,
        8,
        26,
    ),
    status="planned",
    activity_id=None,
):
    return TrainingSession(
        id=uuid4(),
        date=session_date,
        type=session_type,
        sport_type="Run",
        title=session_type,
        description="",
        duration_minutes=50,
        intensity="hard",
        status=status,
        activity_id=activity_id,
    )


def measurement(
    *,
    age_days: int,
    confidence="high",
):
    return PhysiologicalMeasurement(
        id=uuid4(),
        metric="vma",
        value=15.0,
        measured_at=(
            TODAY
            - timedelta(
                days=age_days
            )
        ),
        protocol="half_cooper",
        source="field_test",
        confidence=confidence,
    )


def request(
    *,
    phase=TrainingPhase.BUILD,
):
    return (
        AutomaticPhysiologicalTestProposalRequest(
            athlete_profile_id=(
                ATHLETE_ID
            ),
            reference_date=TODAY,
            week_start=WEEK_START,
            week_end=WEEK_END,
            phase=phase,
            disciplines=(
                SportDiscipline.ROAD_RUNNING,
            ),
        )
    )


def service(
    *,
    current_measurement=None,
    proposals=(),
    sessions=(),
):
    proposal_repository = (
        FakeProposalRepository(
            proposals
        )
    )

    return (
        AutomaticPhysiologicalTestProposalService(
            measurement_repository=(
                FakeMeasurementRepository(
                    current_measurement
                )
            ),
            proposal_repository=(
                proposal_repository
            ),
            training_session_repository=(
                FakeTrainingRepository(
                    sessions
                )
            ),
        ),
        proposal_repository,
    )


def test_missing_vma_and_vo2_session_creates_proposal() -> None:
    vo2 = session(
        "vo2max"
    )

    engine, repository = service(
        sessions=(
            vo2,
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.created is True
    assert result.proposal is not None

    assert (
        result.proposal.protocol
        is PhysiologicalTestType.HALF_COOPER
    )

    assert (
        result.proposal.target_session_id
        == vo2.id
    )

    assert (
        result.proposal.decision
        is PhysiologicalTestDecision.PENDING
    )

    assert len(
        repository.values
    ) == 1


def test_recent_vma_does_not_create_test() -> None:
    engine, repository = service(
        current_measurement=measurement(
            age_days=20
        ),
        sessions=(
            session(
                "vo2max"
            ),
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.created is False
    assert repository.values == []


def test_stale_vma_in_build_creates_test() -> None:
    vo2 = session(
        "vo2max"
    )

    engine, _ = service(
        current_measurement=measurement(
            age_days=100
        ),
        sessions=(
            vo2,
        ),
    )

    result = engine.evaluate_week(
        request(
            phase=TrainingPhase.BUILD
        )
    )

    assert result.created is True


def test_taper_never_creates_vma_test() -> None:
    engine, _ = service(
        current_measurement=measurement(
            age_days=100
        ),
        sessions=(
            session(
                "vo2max"
            ),
        ),
    )

    result = engine.evaluate_week(
        request(
            phase=TrainingPhase.TAPER
        )
    )

    assert result.created is False


def test_recovery_never_creates_vma_test() -> None:
    engine, _ = service(
        current_measurement=None,
        sessions=(
            session(
                "vo2max"
            ),
        ),
    )

    result = engine.evaluate_week(
        request(
            phase=TrainingPhase.RECOVERY
        )
    )

    assert result.created is False


def test_no_compatible_quality_session_creates_nothing() -> None:
    engine, _ = service(
        current_measurement=None,
        sessions=(
            session(
                "aerobic_easy"
            ),
            session(
                "long_endurance"
            ),
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.created is False


def test_vo2max_is_preferred_over_speed_development() -> None:
    speed = session(
        "speed_development",
        session_date=date(
            2026,
            8,
            25,
        ),
    )

    vo2 = session(
        "vo2max",
        session_date=date(
            2026,
            8,
            27,
        ),
    )

    engine, _ = service(
        sessions=(
            speed,
            vo2,
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.proposal is not None

    assert (
        result.proposal.target_session_id
        == vo2.id
    )


def test_completed_quality_session_is_not_replaced() -> None:
    engine, _ = service(
        sessions=(
            session(
                "vo2max",
                status="completed",
            ),
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.created is False


def test_session_with_activity_is_not_replaced() -> None:
    engine, _ = service(
        sessions=(
            session(
                "vo2max",
                activity_id=uuid4(),
            ),
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.created is False


def test_existing_pending_proposal_blocks_duplicate() -> None:
    from opencoach.physiology.testing import (
        PhysiologicalMetric,
    )

    pending = PhysiologicalTestProposal(
        id=uuid4(),
        athlete_profile_id=(
            ATHLETE_ID
        ),
        target_session_id=uuid4(),
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        target_metrics=(
            PhysiologicalMetric.VMA,
        ),
        proposed_date=TODAY,
        reason="Test.",
        recommendation="Test.",
        replacement_stimulus=(
            PhysiologicalTestReplacementStimulus
            .AEROBIC_POWER
        ),
    )

    engine, repository = service(
        proposals=(
            pending,
        ),
        sessions=(
            session(
                "vo2max"
            ),
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.created is False

    assert len(
        repository.values
    ) == 1

def test_recent_decline_blocks_new_test() -> None:
    from opencoach.physiology.testing import (
        PhysiologicalMetric,
    )

    declined = PhysiologicalTestProposal(
        id=uuid4(),
        athlete_profile_id=(
            ATHLETE_ID
        ),
        target_session_id=uuid4(),
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        target_metrics=(
            PhysiologicalMetric.VMA,
        ),
        proposed_date=(
            TODAY
            - timedelta(days=10)
        ),
        reason="Test.",
        recommendation="Test.",
        replacement_stimulus=(
            PhysiologicalTestReplacementStimulus
            .AEROBIC_POWER
        ),
        decision=(
            PhysiologicalTestDecision.DECLINED
        ),
    )

    engine, repository = service(
        proposals=(
            declined,
        ),
        sessions=(
            session(
                "vo2max"
            ),
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.created is False

    assert len(
        repository.values
    ) == 1


def test_old_decline_allows_new_proposal() -> None:
    from opencoach.physiology.testing import (
        PhysiologicalMetric,
    )

    declined = PhysiologicalTestProposal(
        id=uuid4(),
        athlete_profile_id=(
            ATHLETE_ID
        ),
        target_session_id=uuid4(),
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        target_metrics=(
            PhysiologicalMetric.VMA,
        ),
        proposed_date=(
            TODAY
            - timedelta(days=40)
        ),
        reason="Ancien refus.",
        recommendation="Test.",
        replacement_stimulus=(
            PhysiologicalTestReplacementStimulus
            .AEROBIC_POWER
        ),
        decision=(
            PhysiologicalTestDecision.DECLINED
        ),
    )

    engine, repository = service(
        proposals=(
            declined,
        ),
        sessions=(
            session(
                "vo2max"
            ),
        ),
    )

    result = engine.evaluate_week(
        request()
    )

    assert result.created is True

    assert len(
        repository.values
    ) == 2
