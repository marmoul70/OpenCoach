"""Transaction SQL de validation d'une séance réalisée."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models.session_execution_analysis import (
    SessionExecutionAnalysis as AnalysisModel,
)
from opencoach.database.models.training_session import (
    TrainingSession as TrainingSessionModel,
)
from opencoach.models import TrainingSession
from opencoach.training.session_execution.models import (
    SessionExecutionAssessment,
)
from opencoach.training.session_execution.persisted_analysis import (
    PersistedSessionExecutionAnalysis,
)
from opencoach.training.session_execution.validation_writer import (
    TrainingSessionValidationWriter,
)


class TrainingSessionValidationPersistenceError(
    RuntimeError
):
    """Échec de la transaction de validation."""


class SqlTrainingSessionValidationWriter(
    TrainingSessionValidationWriter
):
    """Valide séance + débriefing dans une transaction unique."""

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def persist(
        self,
        *,
        athlete_profile_id: UUID,
        session: TrainingSession,
        assessment: SessionExecutionAssessment,
    ) -> tuple[
        TrainingSession,
        PersistedSessionExecutionAnalysis,
    ]:
        if session.id is None:
            raise TrainingSessionValidationPersistenceError(
                "La séance doit être persistée."
            )

        if assessment.activity_id is None:
            raise TrainingSessionValidationPersistenceError(
                "L'analyse doit posséder une activité."
            )

        goal = assessment.goal_analysis

        if goal is None:
            raise TrainingSessionValidationPersistenceError(
                "L'analyse orientée objectif est absente."
            )

        try:
            database_session = self.db.scalar(
                select(
                    TrainingSessionModel
                ).where(
                    TrainingSessionModel.id
                    == session.id,
                    TrainingSessionModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_session is None:
                raise TrainingSessionValidationPersistenceError(
                    "Séance introuvable."
                )

            # --------------------------------------------------
            # Séance validée
            # --------------------------------------------------

            database_session.activity_id = (
                session.activity_id
            )
            database_session.status = (
                session.status
            )

            # --------------------------------------------------
            # Débriefing courant
            # --------------------------------------------------

            database_analysis = self.db.scalar(
                select(
                    AnalysisModel
                ).where(
                    AnalysisModel.training_session_id
                    == session.id,
                    AnalysisModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_analysis is None:
                database_analysis = AnalysisModel(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    training_session_id=(
                        session.id
                    ),
                    activity_id=(
                        assessment.activity_id
                    ),
                    goal_type=(
                        goal.goal_type.value
                    ),
                    overall_status=(
                        assessment.overall_status.value
                    ),
                    technical_status=None,
                    objective=goal.objective,
                    metrics=[],
                    strengths=[],
                    attention_points=[],
                    debriefing="",
                    derived_results=[],
                )

                self.db.add(
                    database_analysis
                )

            database_analysis.activity_id = (
                assessment.activity_id
            )

            database_analysis.goal_type = (
                goal.goal_type.value
            )

            database_analysis.overall_status = (
                assessment.overall_status.value
            )

            database_analysis.technical_status = (
                assessment.technical_status.value
                if assessment.technical_status
                is not None
                else None
            )

            database_analysis.objective = (
                goal.objective
            )

            database_analysis.metrics = [
                {
                    "key": metric.key,
                    "label": metric.label,
                    "importance": (
                        metric.importance.value
                    ),
                    "status": (
                        metric.status.value
                    ),
                    "target_minimum": (
                        metric.target_minimum
                    ),
                    "target_maximum": (
                        metric.target_maximum
                    ),
                    "unit": metric.unit,
                    "actual_value": (
                        metric.actual_value
                    ),
                    "delta": metric.delta,
                    "delta_percent": (
                        metric.delta_percent
                    ),
                    "message": metric.message,
                }
                for metric
                in goal.metrics
            ]

            database_analysis.strengths = list(
                goal.strengths
            )

            database_analysis.attention_points = list(
                goal.attention_points
            )

            database_analysis.debriefing = (
                goal.debriefing
            )

            database_analysis.derived_results = [
                {
                    "key": key,
                    "value": value,
                }
                for key, value
                in goal.derived_results
            ]

            database_analysis.analyzed_at = (
                datetime.now(
                    timezone.utc
                )
            )

            # --------------------------------------------------
            # UN SEUL COMMIT
            # --------------------------------------------------

            self.db.commit()

            self.db.refresh(
                database_session
            )

            self.db.refresh(
                database_analysis
            )

            return (
                _session_to_domain(
                    database_session
                ),
                _analysis_to_domain(
                    database_analysis
                ),
            )

        except TrainingSessionValidationPersistenceError:
            self.db.rollback()
            raise

        except SQLAlchemyError as exc:
            self.db.rollback()

            raise TrainingSessionValidationPersistenceError(
                "Impossible de valider atomiquement "
                "la séance et son débriefing."
            ) from exc


def _session_to_domain(
    model: TrainingSessionModel,
) -> TrainingSession:
    return TrainingSession(
        id=model.id,
        date=model.date,
        type=model.type,
        sport_type=model.sport_type,
        title=model.title,
        description=model.description,
        duration_minutes=(
            model.duration_minutes
        ),
        planning_key=model.planning_key,
        distance_km=model.distance_km,
        elevation_gain_m=(
            model.elevation_gain_m
        ),
        intensity=model.intensity,
        heart_rate_zone=(
            model.heart_rate_zone
        ),
        prescription=model.prescription,
        status=model.status,
        activity_id=model.activity_id,
    )


def _analysis_to_domain(
    model: AnalysisModel,
) -> PersistedSessionExecutionAnalysis:
    return PersistedSessionExecutionAnalysis(
        id=model.id,
        athlete_profile_id=(
            model.athlete_profile_id
        ),
        training_session_id=(
            model.training_session_id
        ),
        activity_id=model.activity_id,
        goal_type=model.goal_type,
        overall_status=(
            model.overall_status
        ),
        technical_status=(
            model.technical_status
        ),
        objective=model.objective,
        metrics=tuple(
            model.metrics or []
        ),
        strengths=tuple(
            model.strengths or []
        ),
        attention_points=tuple(
            model.attention_points or []
        ),
        debriefing=model.debriefing,
        derived_results=tuple(
            (
                item["key"],
                float(item["value"]),
            )
            for item
            in (
                model.derived_results or []
            )
        ),
        analyzed_at=model.analyzed_at,
    )
