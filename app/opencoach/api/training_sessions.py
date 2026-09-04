from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from opencoach.coaching.session_guidance import (
    SessionGuidanceStep,
    build_session_guidance,
)

from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
)
from opencoach.database.repositories import (
    SqlTrainingSessionRepository,
    TrainingSessionRepositoryError,
)
from opencoach.database.repositories.sql_activity import (
    SqlActivityRepository,
)
from opencoach.database.repositories.sql_activity_detail import (
    SqlActivityDetailRepository,
)
from opencoach.database.repositories.sql_session_execution_analysis import (
    SqlSessionExecutionAnalysisRepository,
)
from opencoach.database.repositories.sql_training_session_validation import (
    SqlTrainingSessionValidationWriter,
    TrainingSessionValidationPersistenceError,
)
from opencoach.database.session import get_db
from opencoach.schemas.training_session import (
    SessionExecutionDebriefResponse,
    SessionExecutionMetricResponse,
    TrainingActivityCandidateResponse,
    TrainingAvailableActivityResponse,
    TrainingSessionActivityUpdate,
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingSessionStatusUpdate,
    TrainingSessionValidateRequest,
    TrainingSessionValidationResponse,
)
from opencoach.config import (
    get_threshold_settings,
)
from opencoach.training import (
    match_activity_to_session,
)
from opencoach.models import TrainingSession
from opencoach.training.session_execution.validation_service import (
    TrainingSessionActivityNotFoundError,
    TrainingSessionAlreadyValidatedError,
    TrainingSessionInvalidPrescriptionError,
    TrainingSessionMissingActivityDetailError,
    TrainingSessionNotFoundError,
    ValidateTrainingSessionService,
)

from opencoach.api.profile import (
    get_profile_service,
)
from opencoach.coaching.manual_session_move import (
    ManualSessionMoveError,
)
from opencoach.coaching.manual_session_move_service import (
    ManualSessionMoveService,
    ManualSessionMoveSessionNotFoundError,
    ManualSessionMoveTargetUnavailableError,
)
from opencoach.database.repositories.sql_athlete_constraint import (
    SqlAthleteConstraintRepository,
)
from opencoach.services import (
    ProfileService,
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
        sport_type=session.sport_type,
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




def _debrief_response(
    analysis,
) -> SessionExecutionDebriefResponse:
    """Convertit un débriefing persistant vers l'API."""

    return SessionExecutionDebriefResponse(
        id=analysis.id,
        training_session_id=(
            analysis.training_session_id
        ),
        activity_id=analysis.activity_id,
        goal_type=analysis.goal_type,
        overall_status=(
            analysis.overall_status
        ),
        technical_status=(
            analysis.technical_status
        ),
        objective=analysis.objective,
        metrics=[
            SessionExecutionMetricResponse(
                key=metric["key"],
                label=metric["label"],
                importance=(
                    metric["importance"]
                ),
                status=metric["status"],
                target_minimum=(
                    metric.get(
                        "target_minimum"
                    )
                ),
                target_maximum=(
                    metric.get(
                        "target_maximum"
                    )
                ),
                unit=metric.get("unit"),
                actual_value=(
                    metric.get(
                        "actual_value"
                    )
                ),
                delta=metric.get(
                    "delta"
                ),
                delta_percent=(
                    metric.get(
                        "delta_percent"
                    )
                ),
                message=metric.get(
                    "message"
                ),
            )
            for metric
            in analysis.metrics
        ],
        strengths=list(
            analysis.strengths
        ),
        attention_points=list(
            analysis.attention_points
        ),
        debriefing=analysis.debriefing,
        derived_results=[
            {
                "key": key,
                "value": value,
            }
            for key, value
            in analysis.derived_results
        ],
        analyzed_at=(
            analysis.analyzed_at
        ),
    )


class SessionGuidanceIntensityTargetResponse(
    BaseModel
):
    reference: str
    label: str

    minimum: float
    maximum: float

    unit: str

    speed_min_kmh: float | None = None
    speed_max_kmh: float | None = None

    pace_fastest_seconds_per_km: float | None = None
    pace_slowest_seconds_per_km: float | None = None


class SessionGuidanceStepResponse(
    BaseModel
):
    title: str
    description: str

    duration_minutes: int | None = None

    intensity_target: str | None = None
    heart_rate_target: str | None = None

    intensity_targets: list[
        SessionGuidanceIntensityTargetResponse
    ] = Field(
        default_factory=list
    )

    repetitions: int | None = None

    work_distance_meters: int | None = None

    repetition_fast_seconds: float | None = None
    repetition_slow_seconds: float | None = None

    recovery_description: str | None = None


class SessionGuidanceResponse(
    BaseModel
):
    session_type: str

    objective: str
    coach_rationale: str

    terrain_recommendation: str

    preparation: list[str]

    warmup: list[
        SessionGuidanceStepResponse
    ]

    main_set: list[
        SessionGuidanceStepResponse
    ]

    cooldown: list[
        SessionGuidanceStepResponse
    ]

    execution_advice: list[str]

    warnings: list[str]

    analysis_targets: list[str]


@router.get(
    "",
    response_model=list[TrainingSessionResponse],
)
def list_training_sessions(
    start: date = Query(...),
    end: date = Query(...),
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
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

@router.post(
    "",
    response_model=TrainingSessionResponse,
    status_code=201,
)
def create_training_session(
    payload: TrainingSessionCreate,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
) -> TrainingSessionResponse:
    """Crée une séance d'entraînement supplémentaire."""

    session = TrainingSession(
        id=None,
        date=payload.date,
        type=payload.type,
        sport_type=payload.sport_type,
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        distance_km=payload.distance_km,
        elevation_gain_m=payload.elevation_gain_m,
        intensity=payload.intensity,
        heart_rate_zone=payload.heart_rate_zone,
        status=payload.status,
        activity_id=payload.activity_id,
    )

    try:
        created_session = repository.save_session(
            athlete_profile_id,
            session,
        )

    except TrainingSessionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de créer la séance.",
        ) from exc

    return to_response(
        created_session,
    )

@router.get(
    "/available-activities",
    response_model=list[
        TrainingAvailableActivityResponse
    ],
)
def list_available_activities(
    session_date: date = Query(
        alias="date",
    ),
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
) -> list[TrainingAvailableActivityResponse]:
    """Retourne les activités non liées disponibles pour une date."""

    try:
        activities = (
            repository
            .list_unlinked_activities_for_date(
                athlete_profile_id,
                session_date,
            )
        )

    except TrainingSessionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de rechercher les "
                "activités disponibles du jour."
            ),
        ) from exc

    return [
        TrainingAvailableActivityResponse(
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
            distance_m=activity.distance_m,
            elevation_gain_m=(
                activity.elevation_gain_m
            ),
            training_load=activity.training_load,
            feel=activity.feel,
        )
        for activity in activities
        if activity.id is not None
    ]

@router.get(
    "/{session_id}",
    response_model=TrainingSessionResponse,
)
def get_training_session(
    session_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
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
        get_current_athlete_profile_id,
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
        get_current_athlete_profile_id,
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
        get_current_athlete_profile_id,
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

    candidates = []

    for activity in activities:
        if activity.id is None:
            continue

        match = match_activity_to_session(
            session,
            activity,
        )

        candidates.append(
            (
                activity,
                match,
            )
        )

    candidates.sort(
        key=lambda item: item[1].score,
        reverse=True,
    )

    thresholds = get_threshold_settings()

    best_match_threshold = (
        thresholds
        .activity_matching
        .best_match_score
    )

    best_activity_id = (
        candidates[0][0].id
        if (
            candidates
            and candidates[0][1].score
            >= best_match_threshold
        )
        else None
    )

    return [
        TrainingActivityCandidateResponse(
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
            distance_m=activity.distance_m,
            elevation_gain_m=activity.elevation_gain_m,
            feel=activity.feel,
            match_score=match.score,
            best_match=(
                activity.id == best_activity_id
            ),
            sport_matches=match.sport_matches,
            sport_score=match.sport_score,
            distance_score=match.distance_score,
            duration_score=match.duration_score,
            elevation_score=match.elevation_score,
        )
        for activity, match in candidates
    ]


@router.get(
    "/{session_id}/guidance",
    response_model=SessionGuidanceResponse,
)
def get_training_session_guidance(
    session_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    db: Session = Depends(get_db),
) -> SessionGuidanceResponse:
    """Retourne la fiche explicative complète d'une séance."""

    repository = (
        SqlTrainingSessionRepository(
            db
        )
    )

    session = repository.get_session(
        athlete_profile_id,
        session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Séance d'entraînement "
                "introuvable."
            ),
        )

    guidance = (
        build_session_guidance(
            session
        )
    )

    def map_step(
        step: SessionGuidanceStep,
    ) -> SessionGuidanceStepResponse:
        return SessionGuidanceStepResponse(
            title=step.title,
            description=(
                step.description
            ),
            duration_minutes=(
                step.duration_minutes
            ),
            intensity_target=(
                step.intensity_target
            ),
            heart_rate_target=(
                step.heart_rate_target
            ),
            intensity_targets=[
                SessionGuidanceIntensityTargetResponse(
                    reference=target.reference,
                    label=target.label,
                    minimum=target.minimum,
                    maximum=target.maximum,
                    unit=target.unit,
                    speed_min_kmh=(
                        target.speed_min_kmh
                    ),
                    speed_max_kmh=(
                        target.speed_max_kmh
                    ),
                    pace_fastest_seconds_per_km=(
                        target.pace_fastest_seconds_per_km
                    ),
                    pace_slowest_seconds_per_km=(
                        target.pace_slowest_seconds_per_km
                    ),
                )
                for target
                in step.intensity_targets
            ],
            repetitions=(
                step.repetitions
            ),
            work_distance_meters=(
                step.work_distance_meters
            ),
            repetition_fast_seconds=(
                step.repetition_fast_seconds
            ),
            repetition_slow_seconds=(
                step.repetition_slow_seconds
            ),
            recovery_description=(
                step.recovery_description
            ),
        )

    return SessionGuidanceResponse(
        session_type=(
            guidance.session_type
        ),
        objective=(
            guidance.objective
        ),
        coach_rationale=(
            guidance.coach_rationale
        ),
        terrain_recommendation=(
            guidance.terrain_recommendation
        ),
        preparation=list(
            guidance.preparation
        ),
        warmup=[
            map_step(step)
            for step
            in guidance.warmup
        ],
        main_set=[
            map_step(step)
            for step
            in guidance.main_set
        ],
        cooldown=[
            map_step(step)
            for step
            in guidance.cooldown
        ],
        execution_advice=list(
            guidance.execution_advice
        ),
        warnings=list(
            guidance.warnings
        ),
        analysis_targets=list(
            guidance.analysis_targets
        ),
    )


@router.post(
    "/{session_id}/validate",
    response_model=(
        TrainingSessionValidationResponse
    ),
)
def validate_training_session(
    session_id: UUID,
    payload: TrainingSessionValidateRequest,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    db: Session = Depends(
        get_db
    ),
) -> TrainingSessionValidationResponse:
    """Valide l'activité choisie explicitement par l'athlète."""

    service = ValidateTrainingSessionService(
        training_session_repository=(
            SqlTrainingSessionRepository(
                db
            )
        ),
        activity_repository=(
            SqlActivityRepository(
                db
            )
        ),
        activity_detail_repository=(
            SqlActivityDetailRepository(
                db
            )
        ),
        validation_writer=(
            SqlTrainingSessionValidationWriter(
                db
            )
        ),
    )

    try:
        result = service.execute(
            athlete_profile_id=(
                athlete_profile_id
            ),
            training_session_id=(
                session_id
            ),
            activity_id=(
                payload.activity_id
            ),
        )

    except (
        TrainingSessionNotFoundError
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except (
        TrainingSessionActivityNotFoundError
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except (
        TrainingSessionAlreadyValidatedError
    ) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except (
        TrainingSessionMissingActivityDetailError
    ) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except (
        TrainingSessionInvalidPrescriptionError
    ) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except (
        TrainingSessionValidationPersistenceError
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de valider "
                "la séance."
            ),
        ) from exc

    return TrainingSessionValidationResponse(
        session=to_response(
            result.session
        ),
        analysis=_debrief_response(
            result.analysis
        ),
    )


@router.get(
    "/{session_id}/debrief",
    response_model=(
        SessionExecutionDebriefResponse
    ),
)
def get_training_session_debrief(
    session_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    db: Session = Depends(
        get_db
    ),
) -> SessionExecutionDebriefResponse:
    """Retourne le débriefing d'une séance validée."""

    repository = (
        SqlSessionExecutionAnalysisRepository(
            db
        )
    )

    try:
        analysis = (
            repository.get_for_session(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                training_session_id=(
                    session_id
                ),
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger "
                "le débriefing."
            ),
        ) from exc

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Aucun débriefing n'existe "
                "pour cette séance."
            ),
        )

    return _debrief_response(
        analysis
    )

class TrainingSessionMoveDayResponse(
    BaseModel
):
    """Évaluation d'un jour possible de déplacement."""

    date: date

    score: int

    selectable: bool
    current: bool

    level: str

    recommended: bool

    reasons: list[str]

    blocking_reasons: list[str]


class TrainingSessionMoveOptionsResponse(
    BaseModel
):
    """Options proposées pour déplacer une séance."""

    source_date: date

    week_start: date
    week_end: date

    best_date: date | None

    days: list[
        TrainingSessionMoveDayResponse
    ]


@router.get(
    "/{session_id}/move-options",
    response_model=(
        TrainingSessionMoveOptionsResponse
    ),
)
def get_training_session_move_options(
    session_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
    profile_service: ProfileService = Depends(
        get_profile_service,
    ),
    db: Session = Depends(
        get_db,
    ),
) -> TrainingSessionMoveOptionsResponse:
    """Prévisualise les jours possibles de déplacement.

    Cette route est strictement en lecture seule.

    Elle ne déplace aucune séance et ne modifie aucun statut.
    """

    service = ManualSessionMoveService(
        training_session_repository=(
            repository
        ),
        athlete_constraint_repository=(
            SqlAthleteConstraintRepository(
                db
            )
        ),
    )

    athlete = (
        profile_service
        .get_profile()
    )

    try:
        plan = service.preview(
            athlete_profile_id=(
                athlete_profile_id
            ),
            athlete=athlete,
            session_id=session_id,
            reference_date=date.today(),
        )

    except (
        ManualSessionMoveSessionNotFoundError
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail="Séance introuvable.",
        ) from exc

    except ManualSessionMoveError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return (
        TrainingSessionMoveOptionsResponse(
            source_date=(
                plan.source_date
            ),
            week_start=(
                plan.week_start
            ),
            week_end=(
                plan.week_end
            ),
            best_date=(
                plan.best_date
            ),
            days=[
                TrainingSessionMoveDayResponse(
                    date=day.date,
                    score=day.score,
                    selectable=(
                        day.selectable
                    ),
                    current=day.current,
                    level=day.level,
                    recommended=(
                        day.recommended
                    ),
                    reasons=list(
                        day.reasons
                    ),
                    blocking_reasons=list(
                        day.blocking_reasons
                    ),
                )
                for day
                in plan.days
            ],
        )
    )

class TrainingSessionMovePayload(
    BaseModel
):
    """Choix explicite d'une nouvelle date."""

    target_date: date


@router.patch(
    "/{session_id}/move",
    response_model=TrainingSessionResponse,
)
def move_training_session(
    session_id: UUID,
    payload: TrainingSessionMovePayload,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository,
    ),
    profile_service: ProfileService = Depends(
        get_profile_service,
    ),
    db: Session = Depends(
        get_db,
    ),
) -> TrainingSessionResponse:
    """Déplace volontairement une séance planifiée.

    Les règles de placement sont recalculées au moment de
    l'écriture afin d'empêcher tout contournement frontend.
    """

    service = ManualSessionMoveService(
        training_session_repository=(
            repository
        ),
        athlete_constraint_repository=(
            SqlAthleteConstraintRepository(
                db
            )
        ),
    )

    athlete = (
        profile_service
        .get_profile()
    )

    try:
        moved = service.move(
            athlete_profile_id=(
                athlete_profile_id
            ),
            athlete=athlete,
            session_id=session_id,
            target_date=(
                payload.target_date
            ),
            reference_date=date.today(),
        )

    except (
        ManualSessionMoveSessionNotFoundError
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail="Séance introuvable.",
        ) from exc

    except (
        ManualSessionMoveTargetUnavailableError,
        ManualSessionMoveError,
    ) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return to_response(
        moved
    )
