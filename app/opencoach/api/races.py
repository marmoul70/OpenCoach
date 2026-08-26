from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
)
from sqlalchemy.orm import Session

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.api.coaching.dependencies import (
    get_current_week_planning_service,
)
from opencoach.coaching.generation import (
    CurrentWeekPlanningService,
)
from opencoach.database.repositories import (
    RaceRepositoryError,
    SqlActivityRepository,
    SqlRaceRepository,
)
from opencoach.database.session import (
    get_db,
)
from opencoach.models import Race
from opencoach.races import (
    RaceActualResult,
    RaceResultService,
)
from opencoach.schemas.race import (
    RaceActivityCandidateResponse,
    RaceActivityUpdate,
    RaceActualResultResponse,
    RaceCreate,
    RaceResponse,
    RaceUpdate,
)


router = APIRouter(
    prefix="/api/races",
    tags=["races"],
)


def race_affects_current_trajectory(
    race: Race,
) -> bool:
    """Indique si la course doit provoquer un refresh du coaching."""

    return (
        race.priority == "primary"
        and race.status == "planned"
    )


def refresh_current_week_for_race(
    *,
    race: Race,
    athlete_profile_id: UUID,
    planning_service: CurrentWeekPlanningService,
) -> None:
    """Régénère la semaine si la course influence la trajectoire."""

    if not race_affects_current_trajectory(
        race
    ):
        return

    planning_service.refresh(
        athlete_profile_id=(
            athlete_profile_id
        ),
        reference_date=date.today(),
        additional_context=(
            "course principale modifiée",
        ),
    )


def get_race_repository(
    db: Session = Depends(
        get_db
    ),
) -> SqlRaceRepository:
    """Construit le repository SQL des courses."""

    return SqlRaceRepository(
        db
    )


def get_activity_repository(
    db: Session = Depends(
        get_db
    ),
) -> SqlActivityRepository:
    """Construit le repository SQL des activités."""

    return SqlActivityRepository(
        db
    )


def to_actual_result_response(
    result: RaceActualResult,
) -> RaceActualResultResponse:
    """Convertit le résultat effectif vers le contrat API."""

    return RaceActualResultResponse(
        source=result.source,
        activity_id=result.activity_id,
        distance_km=result.distance_km,
        elevation_gain_m=(
            result.elevation_gain_m
        ),
        duration_minutes=(
            result.duration_minutes
        ),
        training_load=(
            result.training_load
        ),
    )


def to_response(
    race: Race,
    actual_result: RaceActualResult,
) -> RaceResponse:
    """Convertit une course métier vers sa réponse API."""

    if race.id is None:
        raise RuntimeError(
            (
                "Une course persistée doit "
                "posséder un identifiant."
            )
        )

    return RaceResponse(
        id=race.id,
        date=race.date,
        name=race.name,
        location=race.location,
        race_type=race.race_type,
        priority=race.priority,
        distance_km=race.distance_km,
        elevation_gain_m=(
            race.elevation_gain_m
        ),
        target_time_minutes=(
            race.target_time_minutes
        ),
        status=race.status,
        actual_distance_km=(
            race.actual_distance_km
        ),
        actual_elevation_gain_m=(
            race.actual_elevation_gain_m
        ),
        actual_time_minutes=(
            race.actual_time_minutes
        ),
        ranking=race.ranking,
        notes=race.notes,
        activity_id=race.activity_id,
        actual_result=(
            to_actual_result_response(
                actual_result
            )
        ),
    )


def build_race_response(
    race: Race,
    *,
    athlete_profile_id: UUID,
    activity_repository: SqlActivityRepository,
) -> RaceResponse:
    """Construit la réponse complète d'une course."""

    result_service = RaceResultService(
        activity_repository
    )

    actual_result = (
        result_service.calculate(
            athlete_profile_id,
            race,
        )
    )

    return to_response(
        race,
        actual_result,
    )


def create_domain_race(
    payload: RaceCreate | RaceUpdate,
    *,
    race_id: UUID | None,
) -> Race:
    """Construit le modèle métier depuis un payload API."""

    return Race(
        id=race_id,
        date=payload.date,
        name=payload.name.strip(),
        location=payload.location.strip(),
        race_type=payload.race_type,
        priority=payload.priority,
        distance_km=payload.distance_km,
        elevation_gain_m=(
            payload.elevation_gain_m
        ),
        target_time_minutes=(
            payload.target_time_minutes
        ),
        status=payload.status,
        actual_distance_km=(
            payload.actual_distance_km
        ),
        actual_elevation_gain_m=(
            payload.actual_elevation_gain_m
        ),
        actual_time_minutes=(
            payload.actual_time_minutes
        ),
        ranking=payload.ranking,
        notes=payload.notes.strip(),
        activity_id=payload.activity_id,
    )


@router.get(
    "",
    response_model=list[
        RaceResponse
    ],
)
def list_races(
    start: date | None = Query(
        default=None,
    ),
    end: date | None = Query(
        default=None,
    ),
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlRaceRepository = Depends(
        get_race_repository,
    ),
    activity_repository: SqlActivityRepository = Depends(
        get_activity_repository,
    ),
) -> list[RaceResponse]:
    """Retourne les courses de l'athlète."""

    if (
        start is None
        and end is not None
    ) or (
        start is not None
        and end is None
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Les paramètres start et end "
                "doivent être fournis ensemble."
            ),
        )

    if (
        start is not None
        and end is not None
        and start > end
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "La date de début doit être "
                "antérieure ou égale à la date de fin."
            ),
        )

    try:
        if (
            start is not None
            and end is not None
        ):
            races = (
                repository
                .list_races_between(
                    athlete_profile_id,
                    start,
                    end,
                )
            )

        else:
            races = (
                repository
                .list_races_between(
                    athlete_profile_id,
                    date.min,
                    date.max,
                )
            )

    except RaceRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger les courses."
            ),
        ) from exc

    return [
        build_race_response(
            race,
            athlete_profile_id=(
                athlete_profile_id
            ),
            activity_repository=(
                activity_repository
            ),
        )
        for race in races
    ]


@router.post(
    "",
    response_model=RaceResponse,
    status_code=201,
)
def create_race(
    payload: RaceCreate,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlRaceRepository = Depends(
        get_race_repository,
    ),
    activity_repository: SqlActivityRepository = Depends(
        get_activity_repository,
    ),
    planning_service: CurrentWeekPlanningService = Depends(
        get_current_week_planning_service,
    ),
) -> RaceResponse:
    """Crée une nouvelle course."""

    race = create_domain_race(
        payload,
        race_id=None,
    )

    try:
        created_race = (
            repository.save_race(
                athlete_profile_id,
                race,
            )
        )

    except RaceRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de créer la course."
            ),
        ) from exc

    refresh_current_week_for_race(
        race=created_race,
        athlete_profile_id=(
            athlete_profile_id
        ),
        planning_service=(
            planning_service
        ),
    )

    return build_race_response(
        created_race,
        athlete_profile_id=(
            athlete_profile_id
        ),
        activity_repository=(
            activity_repository
        ),
    )


@router.get(
    "/{race_id}",
    response_model=RaceResponse,
)
def get_race(
    race_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlRaceRepository = Depends(
        get_race_repository,
    ),
    activity_repository: SqlActivityRepository = Depends(
        get_activity_repository,
    ),
) -> RaceResponse:
    """Retourne une course par identifiant."""

    try:
        race = repository.get_race(
            athlete_profile_id,
            race_id,
        )

    except RaceRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger la course."
            ),
        ) from exc

    if race is None:
        raise HTTPException(
            status_code=404,
            detail="Course introuvable.",
        )

    return build_race_response(
        race,
        athlete_profile_id=(
            athlete_profile_id
        ),
        activity_repository=(
            activity_repository
        ),
    )


@router.patch(
    "/{race_id}/activity",
    response_model=RaceResponse,
)
def update_race_activity(
    race_id: UUID,
    payload: RaceActivityUpdate,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlRaceRepository = Depends(
        get_race_repository,
    ),
    activity_repository: SqlActivityRepository = Depends(
        get_activity_repository,
    ),
) -> RaceResponse:
    """Associe ou désassocie une activité à une course."""

    try:
        race = repository.link_activity(
            athlete_profile_id,
            race_id,
            payload.activity_id,
        )

    except RaceRepositoryError as exc:
        message = str(
            exc
        )

        if message in {
            "Course introuvable.",
            "Activité introuvable.",
        }:
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible d'associer "
                "l'activité à la course."
            ),
        ) from exc

    return build_race_response(
        race,
        athlete_profile_id=(
            athlete_profile_id
        ),
        activity_repository=(
            activity_repository
        ),
    )


@router.get(
    "/{race_id}/candidate-activities",
    response_model=list[
        RaceActivityCandidateResponse
    ],
)
def list_race_candidate_activities(
    race_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlRaceRepository = Depends(
        get_race_repository,
    ),
) -> list[
    RaceActivityCandidateResponse
]:
    """Retourne les activités réalisées le jour de la course."""

    try:
        race = repository.get_race(
            athlete_profile_id,
            race_id,
        )

        if race is None:
            raise HTTPException(
                status_code=404,
                detail="Course introuvable.",
            )

        activities = (
            repository
            .list_candidate_activities_for_date(
                athlete_profile_id,
                race.date,
            )
        )

    except HTTPException:
        raise

    except RaceRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de rechercher "
                "les activités du jour de la course."
            ),
        ) from exc

    return [
        RaceActivityCandidateResponse(
            id=activity.id,
            provider=activity.provider,
            provider_activity_id=(
                activity.provider_activity_id
            ),
            name=activity.name,
            sport_type=activity.sport_type,
            start_at_local=(
                activity.start_at_local.isoformat()
                if activity.start_at_local
                else None
            ),
            moving_time_seconds=(
                activity.moving_time_seconds
            ),
            distance_m=(
                activity.distance_m
            ),
            elevation_gain_m=(
                activity.elevation_gain_m
            ),
            training_load=(
                activity.training_load
            ),
            feel=activity.feel,
        )
        for activity in activities
        if activity.id is not None
    ]


@router.put(
    "/{race_id}",
    response_model=RaceResponse,
)
def update_race(
    race_id: UUID,
    payload: RaceUpdate,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlRaceRepository = Depends(
        get_race_repository,
    ),
    activity_repository: SqlActivityRepository = Depends(
        get_activity_repository,
    ),
    planning_service: CurrentWeekPlanningService = Depends(
        get_current_week_planning_service,
    ),
) -> RaceResponse:
    """Met à jour une course complète."""

    try:
        existing = repository.get_race(
            athlete_profile_id,
            race_id,
        )

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="Course introuvable.",
            )

        race = create_domain_race(
            payload,
            race_id=race_id,
        )

        updated_race = (
            repository.save_race(
                athlete_profile_id,
                race,
            )
        )

    except HTTPException:
        raise

    except RaceRepositoryError as exc:
        if (
            str(exc)
            == "Course introuvable."
        ):
            raise HTTPException(
                status_code=404,
                detail="Course introuvable.",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de modifier la course."
            ),
        ) from exc

    refresh_current_week_for_race(
        race=updated_race,
        athlete_profile_id=(
            athlete_profile_id
        ),
        planning_service=(
            planning_service
        ),
    )

    return build_race_response(
        updated_race,
        athlete_profile_id=(
            athlete_profile_id
        ),
        activity_repository=(
            activity_repository
        ),
    )


@router.delete(
    "/{race_id}",
    status_code=204,
)
def delete_race(
    race_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    repository: SqlRaceRepository = Depends(
        get_race_repository,
    ),
) -> Response:
    """Supprime une course."""

    try:
        repository.delete_race(
            athlete_profile_id,
            race_id,
        )

    except RaceRepositoryError as exc:
        if (
            str(exc)
            == "Course introuvable."
        ):
            raise HTTPException(
                status_code=404,
                detail="Course introuvable.",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de supprimer la course."
            ),
        ) from exc

    return Response(
        status_code=204,
    )