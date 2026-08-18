from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.database.repositories import (
    SqlWellnessRepository,
    WellnessRepositoryError,
)
from opencoach.database.session import get_db
from opencoach.models import WellnessDay


router = APIRouter(
    prefix="/api/wellness",
    tags=["wellness"],
)


def get_wellness_repository(
    db: Session = Depends(get_db),
) -> SqlWellnessRepository:
    return SqlWellnessRepository(db)


@router.get("/latest")
def get_latest_wellness(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlWellnessRepository = Depends(
        get_wellness_repository,
    ),
) -> WellnessDay:
    try:
        wellness = repository.get_latest(
            athlete_profile_id,
        )

    except WellnessRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de charger les données Wellness.",
        ) from exc

    if wellness is None:
        raise HTTPException(
            status_code=404,
            detail="Aucune donnée Wellness disponible.",
        )

    return wellness
