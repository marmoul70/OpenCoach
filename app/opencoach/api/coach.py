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
from opencoach.coaching import (
    CoachDecisionAssessment,
    CoachDecisionService,
    CoachDecisionServiceError,
    PlannedSessionUnavailableError,
)
from opencoach.database.repositories import (
    ActivityRepositoryError,
    DailyContextRepositoryError,
    SqlActivityRepository,
    SqlDailyContextRepository,
    SqlTrainingSessionRepository,
    SqlWellnessRepository,
    TrainingSessionRepositoryError,
    WellnessRepositoryError,
)
from opencoach.database.session import get_db
from opencoach.readiness import (
    ReadinessAssessment,
    ReadinessDataUnavailableError,
    ReadinessService,
)
from opencoach.training import (
    DailyTrainingLoadService,
    RecentTrainingLoadService,
    TrainingLoadComparisonService,
)
from opencoach.schemas.coach import (
    CoachDecisionResponse,
    CoachReadinessResponse,
    CoachReadinessSignalResponse,
    CoachRecentLoadAssessmentResponse,
    CoachRecentLoadResponse,
    CoachRecentLoadSignalResponse,
    CoachSessionResponse,
    CoachTodayResponse,
)


router = APIRouter(
    prefix="/api/coach",
    tags=["coach"],
)


def get_coach_decision_service(
    db: Session = Depends(get_db),
) -> CoachDecisionService:
    training_repository = (
        SqlTrainingSessionRepository(
            db
        )
    )

    activity_repository = (
        SqlActivityRepository(
            db
        )
    )

    wellness_repository = (
        SqlWellnessRepository(
            db
        )
    )

    daily_context_repository = (
        SqlDailyContextRepository(
            db
        )
    )

    readiness_service = ReadinessService(
        wellness_repository,
        daily_context_repository=(
            daily_context_repository
        ),
        provider="intervals",
    )

    daily_training_load_service = (
        DailyTrainingLoadService(
            activity_repository,
            training_repository,
        )
    )

    load_comparison_service = (
        TrainingLoadComparisonService(
            training_repository,
            daily_training_load_service,
        )
    )

    recent_load_service = (
        RecentTrainingLoadService(
            load_comparison_service,
        )
    )

    return CoachDecisionService(
        training_repository,
        readiness_service,
        recent_load_service=(
            recent_load_service
        ),
    )

@router.get(
    "/today",
    response_model=CoachTodayResponse,
)
def get_today_coach_decision(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    service: CoachDecisionService = Depends(
        get_coach_decision_service,
    ),
) -> CoachTodayResponse:
    try:
        assessment = service.calculate(
            athlete_profile_id,
            date.today(),
        )

    except PlannedSessionUnavailableError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ReadinessDataUnavailableError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except CoachDecisionServiceError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except (
        ActivityRepositoryError,
        TrainingSessionRepositoryError,
        WellnessRepositoryError,
        DailyContextRepositoryError,
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de calculer "
                "la recommandation du coach."
            ),
        ) from exc

    return _to_response(
        assessment
    )


def _to_response(
    assessment: CoachDecisionAssessment,
) -> CoachTodayResponse:
    session = assessment.session
    readiness = assessment.readiness.readiness
    decision = assessment.decision

    readiness_assessment = (
        assessment.readiness
    )

    recent_load = assessment.recent_load

    recent_load_assessment = (
        assessment.recent_load_assessment
    )

    data_warning = _build_data_warning(
        readiness_assessment
    )

    return CoachTodayResponse(
        date=assessment.date,

        session=(
            CoachSessionResponse(
                id=session.id,
                date=session.date,
                type=session.type,
                sport_type=session.sport_type,
                title=session.title,
                description=session.description,
                duration_minutes=(
                    session.duration_minutes
                ),
                distance_km=session.distance_km,
                elevation_gain_m=(
                    session.elevation_gain_m
                ),
                intensity=session.intensity,
                heart_rate_zone=(
                    session.heart_rate_zone
                ),
                status=session.status,
            )
            if session is not None
            else None
        ),

        readiness=CoachReadinessResponse(
            score=readiness.score,
            level=readiness.level,
            warning_count=(
                readiness.warning_count
            ),
            critical_count=(
                readiness.critical_count
            ),
            training_constraints=list(
                readiness.training_constraints
            ),
            signals=[
                CoachReadinessSignalResponse(
                    metric=signal.metric,
                    level=signal.level,
                    reason=signal.reason,
                    current_value=(
                        signal.current_value
                    ),
                    reference_value=(
                        signal.reference_value
                    ),
                )
                for signal in readiness.signals
            ],
            source_date=(
                readiness_assessment.source_date
            ),
            data_age_days=(
                readiness_assessment.data_age_days
            ),
            data_status=(
                readiness_assessment.data_status
            ),
        ),

        decision=CoachDecisionResponse(
            action=decision.action,
            reason=decision.reason,
            original_duration_minutes=(
                decision.original_duration_minutes
            ),
            recommended_duration_minutes=(
                decision.recommended_duration_minutes
            ),
            duration_factor=(
                decision.duration_factor
            ),
            intensity_factor=(
                decision.intensity_factor
            ),
            original_intensity=(
                decision.original_intensity
            ),
            recommended_intensity=(
                decision.recommended_intensity
            ),
            constraints=list(
                decision.constraints
            ),
        ),

        recent_load=(
            CoachRecentLoadResponse(
                analyzed_days=(
                    recent_load.analyzed_days
                ),
                planned_load_total=(
                    recent_load.planned_load_total
                ),
                actual_load_total=(
                    recent_load.actual_load_total
                ),
                load_delta_total=(
                    recent_load.load_delta_total
                ),
                load_ratio=(
                    recent_load.load_ratio
                ),
                above_plan_days=(
                    recent_load.above_plan_days
                ),
                below_plan_days=(
                    recent_load.below_plan_days
                ),
                on_plan_days=(
                    recent_load.on_plan_days
                ),
                broken_rest_days=(
                    recent_load.broken_rest_days
                ),
                respected_rest_days=(
                    recent_load.respected_rest_days
                ),
                has_training_history=(
                    recent_load.has_training_history
                ),
            )
            if recent_load is not None
            else None
        ),

        recent_load_assessment=(
            CoachRecentLoadAssessmentResponse(
                has_warning=(
                    recent_load_assessment.has_warning
                ),
                has_critical=(
                    recent_load_assessment.has_critical
                ),
                has_overload=(
                    recent_load_assessment.has_overload
                ),
                has_broken_rest=(
                    recent_load_assessment.has_broken_rest
                ),
                signals=[
                    CoachRecentLoadSignalResponse(
                        kind=signal.kind,
                        level=signal.level,
                        reason=signal.reason,
                    )
                    for signal
                    in recent_load_assessment.signals
                ],
            )
            if recent_load_assessment is not None
            else None
        ),

        data_warning=data_warning,
    )

def _build_data_warning(
    readiness_assessment: ReadinessAssessment,
) -> str | None:
    """Construit un avertissement sur la fraîcheur des données."""

    if readiness_assessment.data_status == "fresh":
        return None

    source_date = (
        readiness_assessment
        .source_date
        .strftime("%d/%m/%Y")
    )

    age_days = (
        readiness_assessment.data_age_days
    )

    if age_days == 1:
        age_label = "1 jour"
    else:
        age_label = f"{age_days} jours"

    return (
        "Les données de récupération du jour "
        "ne sont pas encore disponibles. "
        "La recommandation utilise les dernières "
        "données disponibles "
        f"({source_date}, il y a {age_label}) "
        "ainsi que l'historique d'entraînement "
        "enregistré dans OpenCoach."
    )