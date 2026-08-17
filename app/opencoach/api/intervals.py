from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.config import IntervalsSettings
from opencoach.database.models import AthleteProfile, User
from opencoach.database.repositories import (
    ActivityRepositoryError,
    SqlActivityRepository,
)
from opencoach.database.session import get_db
from opencoach.integrations.intervals import (
    IntervalsApiError,
    IntervalsAuthenticationError,
    IntervalsClient,
    IntervalsDataError,
    IntervalsSyncService,
)
from opencoach.services import (
    DEFAULT_SYNC_DAYS,
    IntervalsApplicationService,
)


LOCAL_USER_EMAIL = "local@opencoach.local"


router = APIRouter(
    prefix="/api/integrations/intervals",
    tags=["integrations"],
)


def get_local_athlete_profile_id(
    db: Session = Depends(get_db),
) -> UUID:
    """Retourne l'identifiant du profil sportif local."""

    try:
        statement = (
            select(AthleteProfile.id)
            .join(AthleteProfile.user)
            .where(User.email == LOCAL_USER_EMAIL)
        )

        profile_id = db.scalar(statement)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=503,
            detail="Le stockage OpenCoach est temporairement indisponible.",
        ) from exc

    if profile_id is None:
        raise HTTPException(
            status_code=404,
            detail="Le profil sportif local est introuvable.",
        )

    return profile_id


def get_intervals_application_service(
    db: Session = Depends(get_db),
) -> IntervalsApplicationService:
    """Construit le service applicatif Intervals.icu."""

    try:
        settings = IntervalsSettings.from_env()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="L'intégration Intervals.icu n'est pas configurée.",
        ) from exc

    client = IntervalsClient(
        api_key=settings.api_key,
        athlete_id=settings.athlete_id,
    )

    repository = SqlActivityRepository(db)

    sync_service = IntervalsSyncService(
        client=client,
        repository=repository,
    )

    return IntervalsApplicationService(
        sync_service=sync_service,
    )


@router.post("/sync")
def sync_intervals_activities(
    days: int = Query(
        default=DEFAULT_SYNC_DAYS,
        ge=1,
        le=3650,
    ),
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    service: IntervalsApplicationService = Depends(
        get_intervals_application_service,
    ),
) -> dict[str, str | int]:
    """Synchronise les activités Intervals.icu vers OpenCoach."""

    try:
        synced = service.sync_activities(
            athlete_profile_id,
            days=days,
        )

    except IntervalsAuthenticationError as exc:
        raise HTTPException(
            status_code=502,
            detail="L'authentification auprès d'Intervals.icu a échoué.",
        ) from exc

    except IntervalsApiError as exc:
        raise HTTPException(
            status_code=502,
            detail="Intervals.icu est temporairement indisponible.",
        ) from exc

    except IntervalsDataError as exc:
        raise HTTPException(
            status_code=502,
            detail="Intervals.icu a retourné des données invalides.",
        ) from exc

    except ActivityRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible d'enregistrer les activités.",
        ) from exc

    return {
        "provider": "intervals",
        "synced_activities": synced,
        "days": days,
    }