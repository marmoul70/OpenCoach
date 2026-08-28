from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.database.base import Base
from opencoach.database.models.athlete_profile import (
    AthleteProfile,
)
from opencoach.database.models.user import (
    User,
)
from opencoach.database.models.training_session import (
    TrainingSession,
)
from opencoach.database.repositories.sql_physiological_test_proposal import (
    SqlPhysiologicalTestProposalRepository,
)
from opencoach.physiology.testing import (
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


def create_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(
        engine
    )

    return Session(
        engine
    )


def create_profile(
    db: Session,
) -> AthleteProfile:
    user = User(
        email=(
            f"physiology-test-"
            f"{uuid4()}@opencoach.test"
        ),
    )

    db.add(
        user
    )

    db.flush()

    profile = AthleteProfile(
        user_id=user.id,
    )

    db.add(
        profile
    )

    db.commit()
    db.refresh(
        profile
    )

    return profile


def create_training_session(
    db: Session,
    profile: AthleteProfile,
) -> TrainingSession:
    session = TrainingSession(
        athlete_profile_id=profile.id,
        date=TODAY,
        type="vo2max",
        sport_type="Run",
        title="VO2max",
        description="Séance qualité",
        duration_minutes=50,
        intensity="hard",
        status="planned",
    )

    db.add(
        session
    )

    db.commit()
    db.refresh(
        session
    )

    return session


def create_proposal(
    *,
    athlete_profile_id,
    target_session_id=None,
    proposed_date=TODAY,
) -> PhysiologicalTestProposal:
    return PhysiologicalTestProposal(
        athlete_profile_id=(
            athlete_profile_id
        ),
        target_session_id=(
            target_session_id
        ),
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        target_metrics=(
            PhysiologicalMetric.VMA,
            PhysiologicalMetric.MAX_HEART_RATE,
        ),
        proposed_date=(
            proposed_date
        ),
        reason=(
            "VMA à recalibrer."
        ),
        recommendation=(
            "OpenCoach recommande un Demi-Cooper."
        ),
        replacement_stimulus=(
            PhysiologicalTestReplacementStimulus
            .AEROBIC_POWER
        ),
    )


def test_repository_saves_and_loads_proposal() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalTestProposalRepository(
                db
            )
        )

        saved = repository.save(
            create_proposal(
                athlete_profile_id=(
                    profile.id
                ),
            )
        )

        assert saved.id is not None

        loaded = repository.get(
            profile.id,
            saved.id,
        )

        assert loaded is not None

        assert (
            loaded.protocol
            is PhysiologicalTestType.HALF_COOPER
        )

        assert (
            loaded.decision
            is PhysiologicalTestDecision.PENDING
        )

        assert (
            PhysiologicalMetric.VMA
            in loaded.target_metrics
        )

    finally:
        db.close()


def test_repository_preserves_target_session_id() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        training_session = (
            create_training_session(
                db,
                profile,
            )
        )

        repository = (
            SqlPhysiologicalTestProposalRepository(
                db
            )
        )

        saved = repository.save(
            create_proposal(
                athlete_profile_id=(
                    profile.id
                ),
                target_session_id=(
                    training_session.id
                ),
            )
        )

        assert (
            saved.target_session_id
            == training_session.id
        )

        loaded = repository.get(
            profile.id,
            saved.id,
        )

        assert loaded is not None

        assert (
            loaded.target_session_id
            == training_session.id
        )

    finally:
        db.close()


def test_repository_updates_existing_proposal() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalTestProposalRepository(
                db
            )
        )

        saved = repository.save(
            create_proposal(
                athlete_profile_id=(
                    profile.id
                ),
            )
        )

        accepted = (
            saved.accept()
        )

        updated = repository.save(
            accepted
        )

        assert (
            updated.id
            == saved.id
        )

        assert (
            updated.decision
            is PhysiologicalTestDecision.ACCEPTED
        )

        loaded = repository.get(
            profile.id,
            saved.id,
        )

        assert loaded is not None

        assert (
            loaded.decision
            is PhysiologicalTestDecision.ACCEPTED
        )

    finally:
        db.close()


def test_get_pending_returns_only_pending_proposals() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalTestProposalRepository(
                db
            )
        )

        pending = repository.save(
            create_proposal(
                athlete_profile_id=(
                    profile.id
                ),
            )
        )

        accepted = repository.save(
            create_proposal(
                athlete_profile_id=(
                    profile.id
                ),
                proposed_date=(
                    TODAY
                    + timedelta(days=1)
                ),
            )
            .accept()
        )

        values = (
            repository.get_pending(
                profile.id
            )
        )

        ids = {
            value.id
            for value in values
        }

        assert (
            pending.id
            in ids
        )

        assert (
            accepted.id
            not in ids
        )

    finally:
        db.close()


def test_list_since_filters_old_proposals() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalTestProposalRepository(
                db
            )
        )

        old = repository.save(
            create_proposal(
                athlete_profile_id=(
                    profile.id
                ),
                proposed_date=(
                    TODAY
                    - timedelta(days=60)
                ),
            )
        )

        recent = repository.save(
            create_proposal(
                athlete_profile_id=(
                    profile.id
                ),
                proposed_date=(
                    TODAY
                    - timedelta(days=10)
                ),
            )
        )

        values = repository.list_since(
            profile.id,
            TODAY
            - timedelta(days=28),
        )

        ids = {
            value.id
            for value in values
        }

        assert (
            recent.id
            in ids
        )

        assert (
            old.id
            not in ids
        )

    finally:
        db.close()


def test_repository_is_scoped_to_athlete() -> None:
    db = create_session()

    try:
        first_profile = (
            create_profile(
                db
            )
        )

        second_profile = (
            create_profile(
                db
            )
        )

        repository = (
            SqlPhysiologicalTestProposalRepository(
                db
            )
        )

        saved = repository.save(
            create_proposal(
                athlete_profile_id=(
                    first_profile.id
                ),
            )
        )

        assert (
            repository.get(
                second_profile.id,
                saved.id,
            )
            is None
        )

    finally:
        db.close()
