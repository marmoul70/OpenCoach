from datetime import date, timedelta
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import (
    Race as RaceModel,
)

from opencoach.database.session import (
    get_db,
)

from opencoach.database.repositories.sql_weekly_training_plan import (
    SqlWeeklyTrainingPlanRepository,
)

from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
)
from opencoach.coaching import (
    CoachDecisionAssessment,
    CoachDecisionService,
    CoachDecisionServiceError,
    PlannedSessionUnavailableError,
)
from opencoach.coaching.generation.current_week import (
    current_week_start,
)

from opencoach.coaching.weekly_assessment import (
    CoachWeeklyAssessment,
)
from opencoach.coaching.weekly_assessment_service import (
    CoachWeeklyAssessmentService,
)
from opencoach.api.coaching.dependencies import (
    get_coach_weekly_assessment_service,
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
    CoachSessionDecisionResponse,
    CoachSessionResponse,
    CoachTodayResponse,
    CoachWeeklyAssessmentResponse,
    CoachWeeklyPlanResponse,
    CoachTrajectoryResponse,
    CoachTrajectoryWeekResponse,
)


from opencoach.api.coaching.dependencies import (
    get_weekly_planning_context_builder,
)
from opencoach.coaching.generation.context import (
    WeeklyPlanningContextBuilder,
    WeeklyPlanningContextError,
)
from opencoach.coaching.replanning.preparation_horizon import (
    resolve_preparation_horizon,
)
from opencoach.planning.trajectory.general_development import (
    build_general_development_trajectory,
)

from opencoach.planning.trajectory.service import (
    build_training_trajectory,
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
    "/trajectory",
    response_model=CoachTrajectoryResponse | None,
)
def get_coach_trajectory(
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    context_builder: WeeklyPlanningContextBuilder = Depends(
        get_weekly_planning_context_builder,
    ),
    db: Session = Depends(
        get_db,
    ),
) -> CoachTrajectoryResponse | None:
    """Retourne la progression continue jusqu'à la course principale."""

    today = date.today()

    current_week_start = (
        today
        - timedelta(
            days=today.weekday(),
        )
    )

    race = db.scalar(
        select(
            RaceModel
        )
        .where(
            RaceModel.athlete_profile_id
            == athlete_profile_id,
            RaceModel.date > today,
            RaceModel.priority == "primary",
            RaceModel.status == "planned",
        )
        .order_by(
            RaceModel.date.asc()
        )
        .limit(1)
    )

    if race is None:
        return None

    horizon = resolve_preparation_horizon(
        planning_date=today,
        target_race_date=race.date,
    )

    preparation_start = (
        horizon.preparation_week_start_date
    )

    # Le contexte courant fournit l'historique réel
    # et la baseline utilisés par le moteur.
    prepared = context_builder.build(
        athlete_profile_id=(
            athlete_profile_id
        ),
        planning_date=today,
        trajectory_start_date=(
            current_week_start
        ),
    )

    planning_input = (
        prepared.planning_input
    )

    history_metrics = (
        planning_input
        .trajectory_history_metrics
    )

    # --------------------------------------------------------
    # 1. Maintenance / développement général
    # --------------------------------------------------------

    maintenance_result = (
        build_training_trajectory(
            planning_date=(
                current_week_start
            ),
            target_race_date=None,
            history_metrics=(
                history_metrics
            ),
        )
    )

    maintenance_weeks = [
        week
        for week
        in maintenance_result.trajectory.weeks
        if week.week_start
        < preparation_start
    ]

    # --------------------------------------------------------
    # 2. Préparation spécifique course
    # --------------------------------------------------------

    race_result = (
        build_training_trajectory(
            planning_date=(
                preparation_start
            ),
            target_race_date=(
                race.date
            ),
            target_distance_km=(
                race.distance_km
            ),
            target_elevation_gain_m=(
                race.elevation_gain_m
                or 0.0
            ),
            history_metrics=(
                history_metrics
            ),
        )
    )

    race_weeks = list(
        race_result.trajectory.weeks
    )

    response_weeks: list[
        CoachTrajectoryWeekResponse
    ] = []

    for week in maintenance_weeks:
        response_weeks.append(
            CoachTrajectoryWeekResponse(
                week_start=(
                    week.week_start
                ),
                week_end=(
                    week.week_end
                ),
                mode="maintenance",
                phase=(
                    week.phase.value
                ),
                week_type=(
                    week.week_type.value
                ),
                phase_week_index=(
                    week.phase_week_index
                ),
                target_load=(
                    week.target_load
                ),
                load_min=(
                    week.load_min
                ),
                load_max=(
                    week.load_max
                ),
            )
        )

    for week in race_weeks:
        response_weeks.append(
            CoachTrajectoryWeekResponse(
                week_start=(
                    week.week_start
                ),
                week_end=(
                    week.week_end
                ),
                mode="race_preparation",
                phase=(
                    week.phase.value
                ),
                week_type=(
                    week.week_type.value
                ),
                phase_week_index=(
                    week.phase_week_index
                ),
                target_load=(
                    week.target_load
                ),
                load_min=(
                    week.load_min
                ),
                load_max=(
                    week.load_max
                ),
            )
        )

    return CoachTrajectoryResponse(
        target_race_name=(
            race.name
        ),
        target_race_date=(
            race.date
        ),
        preparation_start_date=(
            preparation_start
        ),
        weeks=response_weeks,
    )


@router.get(
    "/weekly-plan",
    response_model=CoachWeeklyPlanResponse | None,
)
def get_weekly_plan(
    week_start: date,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    db: Session = Depends(
        get_db,
    ),
) -> CoachWeeklyPlanResponse | None:
    """Retourne le plan persistant de la semaine demandée."""

    plan = (
        SqlWeeklyTrainingPlanRepository(
            db
        ).get_plan_for_week(
            athlete_profile_id,
            week_start,
        )
    )

    if plan is None:
        return None

    return CoachWeeklyPlanResponse(
        week_start=plan.week_start,
        week_end=plan.week_end,
        phase=plan.phase,
        week_type=plan.week_type,
        phase_week_index=(
            plan.phase_week_index
        ),
    )


@router.get(
    "/today",
    response_model=CoachTodayResponse,
)
def get_today_coach_decision(
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    service: CoachDecisionService = Depends(
        get_coach_decision_service,
    ),
    weekly_assessment_service: CoachWeeklyAssessmentService = Depends(
        get_coach_weekly_assessment_service,
    ),
    db: Session = Depends(
        get_db,
    ),
) -> CoachTodayResponse:
    try:
        reference_date = date.today()

        assessment = service.calculate(
            athlete_profile_id,
            reference_date,
        )

        weekly_assessment = (
            weekly_assessment_service.calculate(
                athlete_profile_id,
                reference_date,
            )
        )

        weekly_plan = (
            SqlWeeklyTrainingPlanRepository(
                db
            ).get_plan_for_week(
                athlete_profile_id,
                current_week_start(
                    reference_date
                ),
            )
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
        assessment,
        weekly_assessment,
        weekly_plan,
    )


def _to_response(
    assessment: CoachDecisionAssessment,
    weekly_assessment: CoachWeeklyAssessment,
    weekly_plan,
) -> CoachTodayResponse:
    readiness = assessment.readiness.readiness

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

        session_decisions=[
            CoachSessionDecisionResponse(
                session=(
                    CoachSessionResponse(
                        id=item.session.id,
                        date=item.session.date,
                        type=item.session.type,
                        sport_type=(
                            item.session.sport_type
                        ),
                        title=item.session.title,
                        description=(
                            item.session.description
                        ),
                        duration_minutes=(
                            item.session.duration_minutes
                        ),
                        distance_km=(
                            item.session.distance_km
                        ),
                        elevation_gain_m=(
                            item.session.elevation_gain_m
                        ),
                        intensity=(
                            item.session.intensity
                        ),
                        heart_rate_zone=(
                            item.session.heart_rate_zone
                        ),
                        status=item.session.status,
                    )
                    if item.session is not None
                    else None
                ),
                decision=CoachDecisionResponse(
                    action=item.decision.action,
                    reason=item.decision.reason,
                    original_duration_minutes=(
                        item.decision
                        .original_duration_minutes
                    ),
                    recommended_duration_minutes=(
                        item.decision
                        .recommended_duration_minutes
                    ),
                    duration_factor=(
                        item.decision.duration_factor
                    ),
                    intensity_factor=(
                        item.decision.intensity_factor
                    ),
                    original_intensity=(
                        item.decision.original_intensity
                    ),
                    recommended_intensity=(
                        item.decision
                        .recommended_intensity
                    ),
                    constraints=list(
                        item.decision.constraints
                    ),
                ),
            )
            for item
            in assessment.session_decisions
        ],

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

        weekly_assessment=(
            CoachWeeklyAssessmentResponse(
                status=weekly_assessment.status,
                target_load=(
                    weekly_assessment.target_load
                ),
                actual_load_to_date=(
                    weekly_assessment.actual_load_to_date
                ),
                remaining_planned_load=(
                    weekly_assessment.remaining_planned_load
                ),
                projected_week_load=(
                    weekly_assessment.projected_week_load
                ),
                projected_gap=(
                    weekly_assessment.projected_gap
                ),
                projected_gap_percent=(
                    weekly_assessment.projected_gap_percent
                ),
                remaining_days=(
                    weekly_assessment.remaining_days
                ),
                remaining_sessions_count=(
                    weekly_assessment.remaining_sessions_count
                ),
                adaptation_opportunity=(
                    weekly_assessment.adaptation_opportunity
                ),
                adaptation_direction=(
                    weekly_assessment.adaptation_direction
                ),
                history_window_days=(
                    weekly_assessment.history_window_days
                ),
                history_confidence=(
                    weekly_assessment.history_confidence
                ),
                history_confidence_level=(
                    weekly_assessment
                    .history_confidence_level
                ),
                headline=(
                    weekly_assessment.headline
                ),
                analysis=(
                    weekly_assessment.analysis
                ),
                instruction=(
                    weekly_assessment.instruction
                ),
            )
        ),

        weekly_plan=(
            CoachWeeklyPlanResponse(
                week_start=weekly_plan.week_start,
                week_end=weekly_plan.week_end,
                phase=weekly_plan.phase,
                week_type=weekly_plan.week_type,
                phase_week_index=(
                    weekly_plan.phase_week_index
                ),
            )
            if weekly_plan is not None
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
