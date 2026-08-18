from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.database.repositories import (
    SqlTrainingSessionRepository,
    TrainingSessionRepositoryError,
)
from opencoach.database.session import get_db
from opencoach.schemas.training_session import (
    TrainingActivityCandidateResponse,
    TrainingSessionActivityUpdate,
    TrainingSessionResponse,
    TrainingSessionStatusUpdate,
)


router = APIRouter(
    prefix="/api/training-sessions",
    tags=["training"],
)


def get_training_session_repository(
    db: Session = Depends(get_db),
) -> SqlTrainingSessionRepository:
    """Construit le repository SQL des séances."""

    return SqlTrainingSessionRepository(db)


def to_response(
    session,
) -> TrainingSessionResponse:
    """Convertit une séance métier vers sa réponse API."""

    return TrainingSessionResponse(
        id=session.id,
        date=session.date,
        type=session.type,
        title=session.title,
        description=session.description,
        duration_minutes=session.duration_minutes,
        distance_km=session.distance_km,
        elevation_gain_m=session.elevation_gain_m,
        intensity=session.intensity,
        heart_rate_zone=session.heart_rate_zone,
        status=session.status,
        activity_id=session.activity_id,
    )


@router.get(
    "",
    response_model=list[TrainingSessionResponse],
)
def list_training_sessions(
    start: date = Query(...),
    end: date = Query(...),
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
) -> list[TrainingSessionResponse]:
    """Retourne les séances comprises dans une période."""

    try:
        sessions = repository.list_sessions_between(
            athlete_profile_id,
            start,
            end,
        )

    except TrainingSessionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de charger les séances.",
        ) from exc

    return [
        to_response(session)
        for session in sessions
    ]


@router.get(
    "/{session_id}",
    response_model=TrainingSessionResponse,
)
def get_training_session(
    session_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
) -> TrainingSessionResponse:
    """Retourne une séance par identifiant."""

    try:
        session = repository.get_session(
            athlete_profile_id,
            session_id,
        )

    except TrainingSessionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de charger la séance.",
        ) from exc

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Séance introuvable.",
        )

    return to_response(session)


@router.patch(
    "/{session_id}/status",
    response_model=TrainingSessionResponse,
)
def update_training_session_status(
    session_id: UUID,
    payload: TrainingSessionStatusUpdate,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
) -> TrainingSessionResponse:
    """Modifie le statut d'une séance."""

    try:
        session = repository.update_status(
            athlete_profile_id,
            session_id,
            payload.status,
        )

    except TrainingSessionRepositoryError as exc:
        if str(exc) == "Séance introuvable.":
            raise HTTPException(
                status_code=404,
                detail="Séance introuvable.",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail="Impossible de modifier la séance.",
        ) from exc

    return to_response(session)


@router.patch(
    "/{session_id}/activity",
    response_model=TrainingSessionResponse,
)
def update_training_session_activity(
    session_id: UUID,
    payload: TrainingSessionActivityUpdate,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
) -> TrainingSessionResponse:
    """Associe ou désassocie une activité à une séance."""

    try:
        session = repository.link_activity(
            athlete_profile_id,
            session_id,
            payload.activity_id,
        )

    except TrainingSessionRepositoryError as exc:
        message = str(exc)

        if message in {
            "Séance introuvable.",
            "Activité introuvable.",
        }:
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=503,
            detail="Impossible d'associer l'activité.",
        ) from exc

    return to_response(session)


@router.get(
    "/{session_id}/candidate-activities",
    response_model=list[TrainingActivityCandidateResponse],
)
def list_candidate_activities(
    session_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
) -> list[TrainingActivityCandidateResponse]:
    """Retourne les activités réalisées le jour de la séance."""

    try:
        session = repository.get_session(
            athlete_profile_id,
            session_id,
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Séance introuvable.",
            )

        activities = (
            repository.list_candidate_activities_for_date(
                athlete_profile_id,
                session.date,
            )
        )

    except TrainingSessionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de rechercher les activités du jour."
            ),
        ) from exc

    return [
        TrainingActivityCandidateResponse(
            id=activity.id,
            provider=activity.provider,
            provider_activity_id=activity.provider_activity_id,
            name=activity.name,
            sport_type=activity.sport_type,
            start_at_local=(
                activity.start_at_local.isoformat()
                if activity.start_at_local
                else None
            ),
            moving_time_seconds=activity.moving_time_seconds,
            distance_m=activity.distance_m,
            elevation_gain_m=activity.elevation_gain_m,
            feel=activity.feel,
        )
        for activity in activities
        if activity.id is not None
    ]
