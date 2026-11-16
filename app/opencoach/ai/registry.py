"""Composition du registre d'outils métier OpenCoach."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from opencoach.ai.argument_evidence import validate_period_argument_evidence
from opencoach.ai.tool_engine import AIToolRegistry
from opencoach.ai.activity_tools import build_activity_detail_tool
from opencoach.ai.coaching_tools import (
    build_next_planned_session_tool,
    build_planned_sessions_tool,
    build_race_calendar_tool,
    build_training_profile_tool,
    build_weekly_plan_context_tool,
)
from opencoach.ai.constraints_tools import build_active_constraints_tool
from opencoach.ai.execution_tools import build_session_execution_review_tool
from opencoach.ai.load_tools import build_training_load_tool
from opencoach.ai.race_tools import build_race_preparation_tool
from opencoach.ai.recovery_tools import (
    build_recovery_analysis_tool,
    build_recovery_status_tool,
)
from opencoach.ai.training_tools import build_training_history_tool
from opencoach.ai.trend_tools import build_training_trends_tool
from opencoach.database.repositories import (
    SqlActivityDetailRepository,
    SqlActivityRepository,
    SqlTrainingSessionRepository,
)
from opencoach.planning.service import PlanningContextService
from opencoach.services import ActivityDetailService, PlannedTrainingService, RacePreparationService
from opencoach.training import TrainingStatsService
from opencoach.training.session_execution.validation_service import ValidateTrainingSessionService


def build_ai_tool_registry(
    *,
    db: Session,
    athlete_profile_id: UUID,
    training_stats_service: TrainingStatsService,
    context_service: PlanningContextService,
) -> AIToolRegistry:
    """Assemble les adaptateurs autour des capacités Coach existantes."""
    registry = AIToolRegistry(argument_guard=validate_period_argument_evidence)

    training_session_repository = (
        getattr(training_stats_service, "training_session_repository", None)
        or SqlTrainingSessionRepository(db)
    )
    activity_repository = SqlActivityRepository(db)
    activity_detail_repository = SqlActivityDetailRepository(db)

    registry.register(
        build_training_profile_tool(context_service.profile_service)
    )
    registry.register(
        build_active_constraints_tool(
            context_service,
            athlete_profile_id,
        )
    )
    registry.register(
        build_weekly_plan_context_tool(
            context_service,
            athlete_profile_id,
        )
    )
    race_preparation_service = RacePreparationService(
        context_service.race_repository,
        context_service.profile_service,
        training_stats_service,
        athlete_profile_id,
    )
    registry.register(build_race_calendar_tool(race_preparation_service))
    registry.register(build_race_preparation_tool(race_preparation_service))

    planned_training_service = PlannedTrainingService(
        training_session_repository,
        athlete_profile_id,
    )
    registry.register(build_planned_sessions_tool(planned_training_service))
    registry.register(build_next_planned_session_tool(planned_training_service))

    execution_review_service = ValidateTrainingSessionService(
        training_session_repository=training_session_repository,
        activity_repository=activity_repository,
        activity_detail_repository=activity_detail_repository,
    )
    registry.register(
        build_session_execution_review_tool(
            execution_review_service,
            athlete_profile_id,
        )
    )
    registry.register(
        build_activity_detail_tool(
            ActivityDetailService(
                activity_repository,
                activity_detail_repository,
            ),
            athlete_profile_id,
        )
    )
    registry.register(
        build_training_history_tool(
            training_stats_service,
            athlete_profile_id,
        )
    )
    registry.register(
        build_training_load_tool(
            context_service.recent_load_service,
            training_stats_service,
            athlete_profile_id,
        )
    )
    registry.register(
        build_recovery_status_tool(
            context_service.readiness_service,
            athlete_profile_id,
        )
    )
    registry.register(
        build_recovery_analysis_tool(
            context_service.readiness_service,
            athlete_profile_id,
        )
    )
    registry.register(
        build_training_trends_tool(
            training_stats_service,
            athlete_profile_id,
        )
    )
    return registry
