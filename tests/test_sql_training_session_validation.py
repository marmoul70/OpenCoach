from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.base import Base
from opencoach.database.models.session_execution_analysis import (
    SessionExecutionAnalysis as AnalysisModel,
)
from opencoach.database.models.training_session import (
    TrainingSession as TrainingSessionModel,
)
from opencoach.database.repositories.sql_training_session_validation import (
    SqlTrainingSessionValidationWriter,
    TrainingSessionValidationPersistenceError,
)
from opencoach.models import TrainingSession
from opencoach.training.session_execution.goal_analysis.models import (
    GoalComplianceStatus,
    GoalType,
    SessionGoalAnalysis,
)
from opencoach.training.session_execution.models import (
    SessionExecutionAssessment,
    SessionExecutionIntensityAssessment,
    SessionExecutionLoadAssessment,
    SessionExecutionStructureAssessment,
    SessionExecutionVolumeAssessment,
)
from opencoach.training.session_execution.status import (
    AssessmentStatus,
)


def _assessment(
    *,
    session_id,
    activity_id,
):
    goal = SessionGoalAnalysis(
        goal_type=GoalType.ENDURANCE,
        objective="Respecter l'endurance facile.",
        overall_status=(
            GoalComplianceStatus.OK
        ),
        metrics=(),
        strengths=(
            "Intensité respectée.",
        ),
        attention_points=(),
        debriefing=(
            "La séance respecte l'objectif "
            "d'endurance facile."
        ),
    )

    return SessionExecutionAssessment(
        session_id=session_id,
        activity_id=activity_id,
        overall_status=(
            AssessmentStatus.COMPLIANT
        ),
        technical_status=(
            AssessmentStatus.COMPLIANT
        ),
        volume=(
            SessionExecutionVolumeAssessment()
        ),
        intensity=(
            SessionExecutionIntensityAssessment()
        ),
        load=(
            SessionExecutionLoadAssessment()
        ),
        structure=(
            SessionExecutionStructureAssessment()
        ),
        goal_analysis=goal,
    )


def _domain_session(
    *,
    session_id,
    activity_id,
):
    return TrainingSession(
        id=session_id,
        date=date(2026, 8, 29),
        type="aerobic_easy",
        sport_type="Run",
        title="Endurance facile",
        description="EF",
        duration_minutes=45,
        planning_key=(
            "2026-08-29:aerobic_easy"
        ),
        intensity="easy",
        prescription={
            "version": 1,
            "blocks": [],
            "work_structure": {
                "type": "continuous",
                "stimulus": "aerobic_easy",
                "available_minutes": 45,
                "continuous_minutes": 45,
                "description": "EF",
                "circuit": None,
                "intervals": [],
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "rpe",
                        "minimum": 2,
                        "maximum": 4,
                        "unit": "/10",
                    },
                ],
                "guidance": [],
            },
        },
        status="completed",
        activity_id=activity_id,
    )


def _database_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    # Pour ce test transactionnel on ne crée que
    # les deux tables réellement manipulées.
    Base.metadata.create_all(
        engine,
        tables=[
            TrainingSessionModel.__table__,
            AnalysisModel.__table__,
        ],
    )

    return Session(engine)


def _seed_planned_session(
    db,
    *,
    athlete_profile_id,
    session_id,
):
    row = TrainingSessionModel(
        id=session_id,
        athlete_profile_id=(
            athlete_profile_id
        ),
        planning_key=(
            "2026-08-29:aerobic_easy"
        ),
        date=date(2026, 8, 29),
        type="aerobic_easy",
        sport_type="Run",
        title="Endurance facile",
        description="EF",
        duration_minutes=45,
        intensity="easy",
        prescription={
            "version": 1,
        },
        status="planned",
        activity_id=None,
    )

    db.add(row)
    db.commit()


def test_validation_persists_session_and_analysis_together() -> None:
    db = _database_session()

    try:
        athlete_profile_id = uuid4()
        session_id = uuid4()
        activity_id = uuid4()

        _seed_planned_session(
            db,
            athlete_profile_id=(
                athlete_profile_id
            ),
            session_id=session_id,
        )

        writer = (
            SqlTrainingSessionValidationWriter(
                db
            )
        )

        saved_session, analysis = (
            writer.persist(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                session=_domain_session(
                    session_id=session_id,
                    activity_id=activity_id,
                ),
                assessment=_assessment(
                    session_id=session_id,
                    activity_id=activity_id,
                ),
            )
        )

        assert (
            saved_session.status
            == "completed"
        )

        assert (
            saved_session.activity_id
            == activity_id
        )

        assert (
            analysis.training_session_id
            == session_id
        )

        stored_analysis = db.scalar(
            select(
                AnalysisModel
            ).where(
                AnalysisModel.training_session_id
                == session_id
            )
        )

        assert stored_analysis is not None

    finally:
        db.close()


def test_validation_rolls_back_everything_when_commit_fails(
    monkeypatch,
) -> None:
    db = _database_session()

    try:
        athlete_profile_id = uuid4()
        session_id = uuid4()
        activity_id = uuid4()

        _seed_planned_session(
            db,
            athlete_profile_id=(
                athlete_profile_id
            ),
            session_id=session_id,
        )

        writer = (
            SqlTrainingSessionValidationWriter(
                db
            )
        )

        def failing_commit():
            raise SQLAlchemyError(
                "Erreur transactionnelle simulée."
            )

        monkeypatch.setattr(
            db,
            "commit",
            failing_commit,
        )

        with pytest.raises(
            TrainingSessionValidationPersistenceError
        ):
            writer.persist(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                session=_domain_session(
                    session_id=session_id,
                    activity_id=activity_id,
                ),
                assessment=_assessment(
                    session_id=session_id,
                    activity_id=activity_id,
                ),
            )

        stored_session = db.scalar(
            select(
                TrainingSessionModel
            ).where(
                TrainingSessionModel.id
                == session_id
            )
        )

        assert stored_session is not None

        assert (
            stored_session.status
            == "planned"
        )

        assert stored_session.activity_id is None

        stored_analysis = db.scalar(
            select(
                AnalysisModel
            ).where(
                AnalysisModel.training_session_id
                == session_id
            )
        )

        assert stored_analysis is None

    finally:
        db.close()
