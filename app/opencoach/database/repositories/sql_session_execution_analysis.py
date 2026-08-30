"""Repository SQL des débriefings de séances."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models.session_execution_analysis import (
    SessionExecutionAnalysis as SessionExecutionAnalysisModel,
)
from opencoach.training.session_execution.models import (
    SessionExecutionAssessment,
)
from opencoach.training.session_execution.persisted_analysis import (
    PersistedSessionExecutionAnalysis,
)


class SessionExecutionAnalysisRepositoryError(
    RuntimeError
):
    """Erreur de persistance d'un débriefing."""


class SqlSessionExecutionAnalysisRepository:
    """Persiste le résultat du moteur d'analyse de séance."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save(
        self,
        *,
        athlete_profile_id: UUID,
        assessment: SessionExecutionAssessment,
    ) -> PersistedSessionExecutionAnalysis:
        """Crée ou remplace le débriefing courant d'une séance."""

        if assessment.activity_id is None:
            raise SessionExecutionAnalysisRepositoryError(
                "Une activité réalisée est requise "
                "pour persister un débriefing."
            )

        goal = assessment.goal_analysis

        if goal is None:
            raise SessionExecutionAnalysisRepositoryError(
                "L'analyse orientée objectif est absente."
            )

        try:
            database_analysis = self.session.scalar(
                select(
                    SessionExecutionAnalysisModel
                ).where(
                    SessionExecutionAnalysisModel
                    .training_session_id
                    == assessment.session_id,
                    SessionExecutionAnalysisModel
                    .athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_analysis is None:
                database_analysis = (
                    SessionExecutionAnalysisModel(
                        athlete_profile_id=(
                            athlete_profile_id
                        ),
                        training_session_id=(
                            assessment.session_id
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
                )

                self.session.add(
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
                _serialize_metric(metric)
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

            self.session.commit()
            self.session.refresh(
                database_analysis
            )

            return _to_domain(
                database_analysis
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise (
                SessionExecutionAnalysisRepositoryError(
                    "Impossible d'enregistrer "
                    "le débriefing."
                )
            ) from exc

    def get_for_session(
        self,
        *,
        athlete_profile_id: UUID,
        training_session_id: UUID,
    ) -> PersistedSessionExecutionAnalysis | None:
        """Retourne le débriefing courant d'une séance."""

        try:
            database_analysis = self.session.scalar(
                select(
                    SessionExecutionAnalysisModel
                ).where(
                    SessionExecutionAnalysisModel
                    .training_session_id
                    == training_session_id,
                    SessionExecutionAnalysisModel
                    .athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_analysis is None:
                return None

            return _to_domain(
                database_analysis
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise (
                SessionExecutionAnalysisRepositoryError(
                    "Impossible de charger "
                    "le débriefing."
                )
            ) from exc


def _serialize_metric(
    metric,
) -> dict:
    return {
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


def _to_domain(
    model: SessionExecutionAnalysisModel,
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
            model.metrics
            or []
        ),
        strengths=tuple(
            model.strengths
            or []
        ),
        attention_points=tuple(
            model.attention_points
            or []
        ),
        debriefing=model.debriefing,
        derived_results=tuple(
            (
                item["key"],
                float(item["value"]),
            )
            for item
            in (
                model.derived_results
                or []
            )
        ),
        analyzed_at=model.analyzed_at,
    )
