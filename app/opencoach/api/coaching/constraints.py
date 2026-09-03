"""Routes HTTP des contraintes temporaires de l'athlète."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from sqlalchemy.orm import Session

from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
)
from opencoach.coaching.constraint_planning import (
    AthleteConstraintPlanningService,
)
from opencoach.database.repositories import (
    AthleteConstraintRepositoryError,
    SqlAthleteConstraintRepository,
)
from opencoach.database.session import (
    get_db,
)
from opencoach.models import (
    AthleteConstraint,
)

from .dependencies import (
    get_athlete_constraint_planning_service,
)


router = APIRouter(
    prefix="/api/coach/constraints",
    tags=[
        "coach",
        "constraints",
    ],
)


class AthleteConstraintPayload(
    BaseModel
):
    """Données modifiables d'une contrainte temporaire."""

    model_config = ConfigDict(
        extra="forbid",
    )

    start_date: date
    end_date: date

    constraint_type: str

    availability: str

    running_allowed: bool = True

    cross_training_allowed: bool = True

    max_duration_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    notes: str | None = None


class AthleteConstraintResponse(
    BaseModel
):
    """Représentation HTTP d'une contrainte."""

    id: UUID

    start_date: date
    end_date: date

    constraint_type: str
    availability: str

    running_allowed: bool
    cross_training_allowed: bool

    max_duration_minutes: int | None

    notes: str | None


def _to_response(
    constraint: AthleteConstraint,
) -> AthleteConstraintResponse:
    return AthleteConstraintResponse(
        id=constraint.id,
        start_date=constraint.start_date,
        end_date=constraint.end_date,
        constraint_type=(
            constraint.constraint_type
        ),
        availability=(
            constraint.availability
        ),
        running_allowed=(
            constraint.running_allowed
        ),
        cross_training_allowed=(
            constraint.cross_training_allowed
        ),
        max_duration_minutes=(
            constraint.max_duration_minutes
        ),
        notes=constraint.notes,
    )


def _to_domain(
    *,
    constraint_id: UUID,
    payload: AthleteConstraintPayload,
) -> AthleteConstraint:
    try:
        return AthleteConstraint(
            id=constraint_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            constraint_type=(
                payload.constraint_type
            ),
            availability=(
                payload.availability
            ),
            running_allowed=(
                payload.running_allowed
            ),
            cross_training_allowed=(
                payload.cross_training_allowed
            ),
            max_duration_minutes=(
                payload.max_duration_minutes
            ),
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc


@router.post(
    "",
    response_model=(
        AthleteConstraintResponse
    ),
    status_code=status.HTTP_201_CREATED,
)
def create_constraint(
    payload: AthleteConstraintPayload,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    service: AthleteConstraintPlanningService = Depends(
        get_athlete_constraint_planning_service
    ),
) -> AthleteConstraintResponse:
    """Crée une contrainte et adapte la semaine si nécessaire."""

    constraint = _to_domain(
        constraint_id=uuid4(),
        payload=payload,
    )

    try:
        saved = service.save(
            athlete_profile_id=(
                athlete_profile_id
            ),
            constraint=constraint,
            reference_date=date.today(),
        )
    except AthleteConstraintRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible d'enregistrer "
                "la contrainte temporaire."
            ),
        ) from exc

    return _to_response(
        saved
    )


@router.put(
    "/{constraint_id}",
    response_model=(
        AthleteConstraintResponse
    ),
)
def update_constraint(
    constraint_id: UUID,
    payload: AthleteConstraintPayload,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    service: AthleteConstraintPlanningService = Depends(
        get_athlete_constraint_planning_service
    ),
) -> AthleteConstraintResponse:
    """Modifie une contrainte et recalcule la semaine."""

    constraint = _to_domain(
        constraint_id=constraint_id,
        payload=payload,
    )

    try:
        saved = service.save(
            athlete_profile_id=(
                athlete_profile_id
            ),
            constraint=constraint,
            reference_date=date.today(),
        )
    except AthleteConstraintRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de modifier "
                "la contrainte temporaire."
            ),
        ) from exc

    return _to_response(
        saved
    )


@router.delete(
    "/{constraint_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
def delete_constraint(
    constraint_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    service: AthleteConstraintPlanningService = Depends(
        get_athlete_constraint_planning_service
    ),
) -> Response:
    """Supprime une contrainte et recalcule si nécessaire."""

    try:
        service.delete(
            athlete_profile_id=(
                athlete_profile_id
            ),
            constraint_id=(
                constraint_id
            ),
            reference_date=date.today(),
        )
    except AthleteConstraintRepositoryError as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Contrainte temporaire introuvable."
            ),
        ) from exc

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


@router.get(
    "",
    response_model=list[
        AthleteConstraintResponse
    ],
)
def list_current_week_constraints(
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    db: Session = Depends(
        get_db
    ),
) -> list[
    AthleteConstraintResponse
]:
    """Retourne les contraintes chevauchant la semaine courante."""

    today = date.today()

    week_start = (
        today
        - timedelta(
            days=today.weekday()
        )
    )

    week_end = (
        week_start
        + timedelta(days=6)
    )

    repository = (
        SqlAthleteConstraintRepository(
            db
        )
    )

    try:
        constraints = (
            repository.list_overlapping(
                athlete_profile_id,
                week_start,
                week_end,
            )
        )
    except AthleteConstraintRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger "
                "les contraintes temporaires."
            ),
        ) from exc

    return [
        _to_response(
            constraint
        )
        for constraint in constraints
    ]
