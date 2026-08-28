"""Routes HTTP de génération hebdomadaire du coach OpenCoach."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.coaching.generation import (
    ExistingTrainingSessionConflictError,
    GeneratePlannedTrainingWeekService,
    WeeklyPlanningContextBuilder,
    WeeklyPlanningContextError,
    WeeklyTrainingGenerationError,
    WeeklyTrainingPersistenceError,
)
from opencoach.database.repositories import (
    ActivityRepositoryError,
    AthleteConstraintRepositoryError,
    DailyContextRepositoryError,
    PhysiologicalMeasurementRepositoryError,
    ProfileRepositoryError,
    RaceRepositoryError,
    TrainingSessionRepositoryError,
    WellnessRepositoryError,
)

from .dependencies import (
    get_generate_planned_training_week_service,
    get_weekly_planning_context_builder,
)
from .schemas import (
    GenerateTrainingWeekRequest,
    GenerateTrainingWeekResponse,
    GeneratedTrainingSessionResponse,
)


router = APIRouter(
    prefix="/api/coach",
    tags=[
        "coach",
    ],
)


@router.post(
    "/weeks/{week_start}/generate",
    response_model=(
        GenerateTrainingWeekResponse
    ),
)
def generate_training_week(
    week_start: date,
    payload: GenerateTrainingWeekRequest,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id
    ),
    context_builder: WeeklyPlanningContextBuilder = Depends(
        get_weekly_planning_context_builder
    ),
    generation_service: GeneratePlannedTrainingWeekService = Depends(
        get_generate_planned_training_week_service
    ),
) -> GenerateTrainingWeekResponse:
    """Génère et persiste une semaine complète d'entraînement."""

    if week_start.weekday() != 0:
        raise HTTPException(
            status_code=422,
            detail=(
                "week_start doit correspondre "
                "à un lundi."
            ),
        )

    trajectory_start_date = (
        payload.trajectory_start_date
        if payload.trajectory_start_date
        is not None
        else week_start
    )

    if trajectory_start_date > week_start:
        raise HTTPException(
            status_code=422,
            detail=(
                "trajectory_start_date ne peut "
                "pas être postérieure à week_start."
            ),
        )

    try:
        prepared = (
            context_builder.build(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                planning_date=(
                    week_start
                ),
                trajectory_start_date=(
                    trajectory_start_date
                ),
            )
        )

        result = (
            generation_service.execute(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                planning_input=(
                    prepared.planning_input
                ),
                physiological_reference_date=(
                    week_start
                ),
                sport_disciplines=(
                    prepared.sport_disciplines
                ),
                additional_context=tuple(
                    payload.additional_context
                ),
            )
        )

    except WeeklyPlanningContextError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(
                exc
            ),
        ) from exc

    except ExistingTrainingSessionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(
                exc
            ),
        ) from exc

    except (
        WeeklyTrainingGenerationError,
        WeeklyTrainingPersistenceError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc

    except (
        ActivityRepositoryError,
        AthleteConstraintRepositoryError,
        DailyContextRepositoryError,
        PhysiologicalMeasurementRepositoryError,
        ProfileRepositoryError,
        RaceRepositoryError,
        TrainingSessionRepositoryError,
        WellnessRepositoryError,
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de générer "
                "la semaine d'entraînement."
            ),
        ) from exc

    generated_week = (
        result.generation.generated_week
    )

    persisted_sessions = (
        result.generation.persisted_sessions
    )

    return GenerateTrainingWeekResponse(
        week_start=(
            generated_week.week_start
        ),
        week_end=(
            generated_week.week_end
        ),
        phase=(
            generated_week.phase.value
        ),
        target_load=(
            generated_week.target_load
        ),
        session_count=(
            result.session_count
        ),
        sessions=[
            GeneratedTrainingSessionResponse(
                id=session.id,
                planning_key=(
                    session.planning_key
                ),
                date=session.date,
                type=session.type,
                sport_type=(
                    session.sport_type
                ),
                title=session.title,
                description=(
                    session.description
                ),
                duration_minutes=(
                    session.duration_minutes
                ),
                intensity=(
                    session.intensity
                ),
                heart_rate_zone=(
                    session.heart_rate_zone
                ),
                status=session.status,
            )
            for session
            in persisted_sessions
            if session.id is not None
        ],
    )
