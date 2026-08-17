from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.database.repositories import (
    ActivityRepositoryError,
    SqlActivityRepository,
)
from opencoach.database.session import get_db
from opencoach.models import Activity


router = APIRouter(
    prefix="/api/activities",
    tags=["activities"],
)


def get_activity_repository(
    db: Session = Depends(get_db),
) -> SqlActivityRepository:
    return SqlActivityRepository(db)


@router.get("")
def list_activities(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlActivityRepository = Depends(
        get_activity_repository,
    ),
) -> list[Activity]:
    try:
        return repository.list_activities(
            athlete_profile_id,
        )
    except ActivityRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de charger les activités.",
        ) from exc