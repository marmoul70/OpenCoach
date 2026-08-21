from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.database.repositories import (
    ActivityRepositoryError,
    SqlActivityRepository,
    SqlTrainingSessionRepository,
    TrainingSessionRepositoryError,
)
from opencoach.database.session import get_db
from opencoach.schemas.training_stats import (
    TrainingStatsResponse,
)
from opencoach.training import (
    TrainingStatsService,
)


router = APIRouter(
    prefix="/api/training-stats",
    tags=["training"],
)


def get_training_stats_service(
    db: Session = Depends(get_db),
) -> TrainingStatsService:
    """Construit le service de statistiques d'entraînement."""

    return TrainingStatsService(
        activity_repository=(
            SqlActivityRepository(db)
        ),
        training_session_repository=(
            SqlTrainingSessionRepository(db)
        ),
    )


@router.get(
    "",
    response_model=TrainingStatsResponse,
)
def get_training_stats(
    start: date = Query(...),
    end: date = Query(...),
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    service: TrainingStatsService = Depends(
        get_training_stats_service,
    ),
) -> TrainingStatsResponse:
    """Retourne les statistiques réellement effectuées."""

    try:
        stats = service.calculate(
            athlete_profile_id,
            start,
            end,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except (
        ActivityRepositoryError,
        TrainingSessionRepositoryError,
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de calculer "
                "les statistiques d'entraînement."
            ),
        ) from exc

    return TrainingStatsResponse(
        start_date=stats.start_date,
        end_date=stats.end_date,
        activities_count=(
            stats.activities_count
        ),
        manual_sessions_count=(
            stats.manual_sessions_count
        ),
        sessions_count=(
            stats.sessions_count
        ),
        total_duration_minutes=(
            stats.total_duration_minutes
        ),
        total_distance_km=(
            stats.total_distance_km
        ),
        total_elevation_gain_m=(
            stats.total_elevation_gain_m
        ),
        measured_load=(
            stats.measured_load
        ),
        estimated_load=(
            stats.estimated_load
        ),
        total_load=(
            stats.total_load
        ),
    )
