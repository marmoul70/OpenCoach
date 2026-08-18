from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.database.repositories import (
    DailyContextRepositoryError,
    SqlDailyContextRepository,
)
from opencoach.database.session import get_db
from opencoach.models import DailyContext
from opencoach.schemas.daily_context import (
    DailyContextResponse,
    DailyContextUpdate,
)


router = APIRouter(
    prefix="/api/daily-context",
    tags=["daily-context"],
)


def get_daily_context_repository(
    db: Session = Depends(get_db),
) -> SqlDailyContextRepository:
    return SqlDailyContextRepository(
        db
    )


@router.get(
    "/today",
    response_model=DailyContextResponse,
)
def get_today_daily_context(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlDailyContextRepository = Depends(
        get_daily_context_repository,
    ),
) -> DailyContextResponse:
    try:
        context = repository.get_by_date(
            athlete_profile_id,
            date.today(),
        )

    except DailyContextRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger "
                "le contexte quotidien."
            ),
        ) from exc

    if context is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Aucun contexte quotidien "
                "disponible pour aujourd'hui."
            ),
        )

    return _to_response(
        context
    )


@router.put(
    "/today",
    response_model=DailyContextResponse,
)
def update_today_daily_context(
    payload: DailyContextUpdate,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlDailyContextRepository = Depends(
        get_daily_context_repository,
    ),
) -> DailyContextResponse:
    context = DailyContext(
        date=date.today(),
        fatigue_subjective=(
            payload.fatigue_subjective
        ),
        pain_level=payload.pain_level,
        illness_status=payload.illness_status,
        treatment_impact=(
            payload.treatment_impact
        ),
        motivation=payload.motivation,
        notes=payload.notes,
    )

    try:
        saved = repository.save(
            athlete_profile_id,
            context,
        )

    except DailyContextRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible d'enregistrer "
                "le contexte quotidien."
            ),
        ) from exc

    return _to_response(
        saved
    )


def _to_response(
    context: DailyContext,
) -> DailyContextResponse:
    return DailyContextResponse(
        date=context.date.isoformat(),
        fatigue_subjective=(
            context.fatigue_subjective
        ),
        pain_level=context.pain_level,
        illness_status=context.illness_status,
        treatment_impact=context.treatment_impact,
        motivation=context.motivation,
        notes=context.notes,
    )
