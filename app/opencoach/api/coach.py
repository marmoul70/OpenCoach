from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta
from enum import Enum
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
from opencoach.database.models.weekly_debrief import WeeklyDebriefRecord

from opencoach.database.session import get_db

from opencoach.database.repositories.sql_weekly_training_plan import (
    SqlWeeklyTrainingPlanRepository,
)
from opencoach.database.repositories.sql_weekly_debrief import (
    SqlWeeklyDebriefRepository,
)
from opencoach.database.repositories.sql_activity_detail import (
    SqlActivityDetailRepository,
)
from opencoach.database.repositories.sql_coros_daily_data import (
    SqlCorosDailyDataRepository,
)
from opencoach.recovery_assessment import aggregate_coros_time_series

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
from opencoach.coaching.weekly_adaptation import build_weekly_adaptation_decision
from opencoach.coaching.weekly_debrief_planning_application import (
    WeeklyDebriefPlanningApplicationService,
)

from opencoach.coaching.weekly_assessment import (
    CoachWeeklyAssessment,
)
from opencoach.coaching.weekly_assessment_service import (
    CoachWeeklyAssessmentService,
)
from opencoach.api.coaching.dependencies import (
    get_coach_decision_service,
    get_coach_weekly_assessment_service,
    get_weekly_planning_context_builder,
    get_generate_planned_training_week_service,
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
from opencoach.readiness import (
    ReadinessAssessment,
    ReadinessDataUnavailableError,
    ReadinessService,
)
from opencoach.recovery_assessment import (
    build_recovery_assessment,
    recovery_assessment_to_dict,
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
    CoachWeeklyDebriefResponse,
    CoachWeeklyPlanResponse,
    CoachTrajectoryResponse,
    CoachTrajectoryWeekResponse,
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


def _weekly_debrief_json(value):
    """Convertit les objets métier en valeurs JSON compatibles."""

    if isinstance(value, Enum):
        return value.value

    if is_dataclass(value):
        return _weekly_debrief_json(asdict(value))

    if isinstance(value, dict):
        return {
            str(key): _weekly_debrief_json(item)
            for key, item in value.items()
        }

    if isinstance(value, (tuple, list, set, frozenset)):
        return [
            _weekly_debrief_json(item)
            for item in value
        ]

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    return value


@router.get("/weekly-debriefs")
def list_weekly_debriefs(
    limit: int = 26,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Liste les semaines pour lesquelles un bilan persistant existe."""

    safe_limit = min(max(limit, 1), 104)
    records = db.scalars(
        select(WeeklyDebriefRecord)
        .where(
            WeeklyDebriefRecord.athlete_profile_id
            == athlete_profile_id
        )
        .order_by(
            WeeklyDebriefRecord.week_start.desc()
        )
        .limit(safe_limit)
    ).all()

    return [
        {
            "week_start": record.week_start.isoformat(),
            "week_end": record.week_end.isoformat(),
            "verdict": record.verdict,
            "overall_score": record.overall_score,
            "planning_updated": (
                record.planning_updated_at is not None
            ),
        }
        for record in records
    ]


@router.get("/weekly-debrief")
def get_weekly_debrief(
    week_start: date,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    db: Session = Depends(get_db),
) -> dict:
    """Retourne le bilan, ses indicateurs et les flux FC disponibles."""

    stored = SqlWeeklyDebriefRepository(db).get_for_week(
        athlete_profile_id,
        week_start,
    )
    if stored is None:
        raise HTTPException(
            status_code=404,
            detail="Aucun bilan pour cette semaine.",
        )

    activities = SqlActivityRepository(db).list_activities_between(
        athlete_profile_id,
        stored.facts.week_start,
        stored.facts.week_end,
    )

    # Les métriques quotidiennes sont lues depuis le référentiel Wellness
    # déjà alimenté par les intégrations ; aucun snapshot n'est recopié.
    wellness_days = SqlWellnessRepository(db).list_range(
        athlete_profile_id,
        stored.facts.week_start,
        stored.facts.week_end,
    )
    coros_snapshots = SqlCorosDailyDataRepository(db).list_time_series_snapshots(
        athlete_profile_id,
        stored.facts.week_start,
        stored.facts.week_end,
    )
    coros_time_series = aggregate_coros_time_series(
        coros_snapshots,
        start_date=stored.facts.week_start,
        end_date=stored.facts.week_end,
    )
    wellness_payload = [
        {
            "date": day.date.isoformat(),
            "provider": day.provider,
            "resting_hr": day.resting_hr,
            "avg_hr": day.avg_hr,
            "min_hr": day.min_hr,
            "max_hr": day.max_hr,
            "hrv": day.hrv,
            "hrv_baseline": day.hrv_baseline,
            "stress_avg": day.stress_avg,
            "sleep_seconds": day.sleep_seconds,
            "sleep_score": day.sleep_score,
            "sleep_quality": day.sleep_quality,
            "sleep_deep_seconds": day.sleep_deep_seconds,
            "sleep_light_seconds": day.sleep_light_seconds,
            "sleep_rem_seconds": day.sleep_rem_seconds,
            "sleep_awake_seconds": day.sleep_awake_seconds,
            "avg_sleeping_hr": day.avg_sleeping_hr,
            "spo2": day.spo2,
            "steps": day.steps,
        }
        for day in wellness_days
    ]
    detail_repository = SqlActivityDetailRepository(db)
    heart_rate_activities = []

    for activity in activities:
        if activity.id is None:
            continue

        detail = detail_repository.get_activity_detail(
            athlete_profile_id,
            activity.id,
        )
        heart_rates = (
            list(detail.streams.heartrate.data)
            if detail is not None
            and detail.streams.heartrate is not None
            else []
        )
        times = (
            list(detail.streams.time.data)
            if detail is not None
            and detail.streams.time is not None
            else list(range(len(heart_rates)))
        )
        samples = [
            {
                "time_seconds": times[index],
                "bpm": heart_rates[index],
            }
            for index in range(min(len(times), len(heart_rates)))
        ]

        if (
            not samples
            and activity.average_heart_rate is None
            and activity.max_heart_rate is None
        ):
            continue

        heart_rate_activities.append(
            {
                "activity_name": activity.name,
                "started_at": (
                    activity.start_at_local.isoformat()
                    if activity.start_at_local is not None
                    else activity.start_at.isoformat()
                ),
                "average_bpm": activity.average_heart_rate,
                "maximum_bpm": activity.max_heart_rate,
                "sample_count": len(samples),
                "samples": samples,
            }
        )

    return {
        "id": str(stored.id),
        "facts": _weekly_debrief_json(stored.facts),
        "debrief": _weekly_debrief_json(stored.debrief),
        "adaptation": _weekly_debrief_json(
            build_weekly_adaptation_decision(stored.debrief)
        ),
        "heart_rate_activities": heart_rate_activities,
        "wellness_days": wellness_payload,
        "coros_time_series": _weekly_debrief_json(coros_time_series),
        "generated_at": stored.generated_at.isoformat(),
        "planning_updated": (
            stored.planning_updated_at is not None
        ),
    }


@router.post("/weekly-debrief/apply")
def apply_weekly_debrief_adaptation(
    week_start: date,
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id
    ),
    context_builder: WeeklyPlanningContextBuilder = Depends(
        get_weekly_planning_context_builder
    ),
    planning_service=Depends(
        get_generate_planned_training_week_service
    ),
    db: Session = Depends(get_db),
) -> dict:
    """Applique la proposition uniquement après validation explicite."""

    next_week_start = week_start + timedelta(days=7)

    try:
        prepared = context_builder.build(
            athlete_profile_id=athlete_profile_id,
            planning_date=next_week_start,
            trajectory_start_date=next_week_start,
        )
        result = WeeklyDebriefPlanningApplicationService(
            debrief_repository=SqlWeeklyDebriefRepository(db),
            planning_service=planning_service,
        ).execute(
            athlete_profile_id=athlete_profile_id,
            closed_week_start=week_start,
            planning_input=prepared.planning_input,
            reconcile_from_date=next_week_start,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "Impossible d’appliquer la proposition. "
                "Le planning n’a pas été confirmé."
            ),
        ) from exc

    return {
        "week_start": week_start.isoformat(),
        "applied": not result.already_applied,
    }


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

        week_start = current_week_start(
            reference_date
        )

        weekly_plan = (
            SqlWeeklyTrainingPlanRepository(
                db
            ).get_plan_for_week(
                athlete_profile_id,
                week_start,
            )
        )

        debrief_repository = (
            SqlWeeklyDebriefRepository(
                db
            )
        )

        weekly_debrief = (
            debrief_repository.get_for_week(
                athlete_profile_id,
                week_start,
            )
        )

        if weekly_debrief is None:
            weekly_debrief = (
                debrief_repository.get_for_week(
                    athlete_profile_id,
                    week_start
                    - timedelta(days=7),
                )
            )

        recovery_wellness_days = SqlWellnessRepository(db).list_range(
            athlete_profile_id,
            reference_date - timedelta(days=29),
            reference_date,
        )
        from opencoach.wellness_aggregation import aggregate_wellness_days
        recovery_aggregation = aggregate_wellness_days(recovery_wellness_days)
        recovery_assessment = build_recovery_assessment(
            wellness_days=list(recovery_aggregation.days),
            target_date=reference_date,
            provider="opencoach",
            subjective_context=assessment.readiness.context,
        )
        recovery_payload = recovery_assessment_to_dict(recovery_assessment)
        recovery_payload["data_store"] = "OpenCoach"
        recovery_payload["metric_sources"] = recovery_aggregation.metric_sources
        recovery_payload["conflicting_metrics"] = recovery_aggregation.conflicts

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
        weekly_debrief,
        recovery_payload,
    )


def _to_response(
    assessment: CoachDecisionAssessment,
    weekly_assessment: CoachWeeklyAssessment,
    weekly_plan,
    weekly_debrief,
    recovery_payload: dict,
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

        weekly_debrief=(
            CoachWeeklyDebriefResponse(
                week_start=(
                    weekly_debrief
                    .facts.week_start
                ),
                week_end=(
                    weekly_debrief
                    .facts.week_end
                ),
                verdict=(
                    weekly_debrief
                    .debrief.verdict.value
                ),
                adaptation_direction=(
                    weekly_debrief
                    .debrief
                    .adaptation_direction
                    .value
                ),
                overall_score=(
                    weekly_debrief
                    .debrief.overall_score
                ),
                adherence_score=(
                    weekly_debrief
                    .debrief.adherence_score
                ),
                duration_score=(
                    weekly_debrief
                    .debrief.duration_score
                ),
                load_score=(
                    weekly_debrief
                    .debrief.load_score
                ),
                key_sessions_score=(
                    weekly_debrief
                    .debrief.key_sessions_score
                ),
                intensity_score=(
                    weekly_debrief
                    .debrief.intensity_score
                ),
                completion_ratio=(
                    weekly_debrief
                    .debrief.completion_ratio
                ),
                duration_ratio=(
                    weekly_debrief
                    .debrief.duration_ratio
                ),
                load_ratio=(
                    weekly_debrief
                    .debrief.load_ratio
                ),
                headline=(
                    weekly_debrief
                    .debrief.headline
                ),
                analysis=(
                    weekly_debrief
                    .debrief.analysis
                ),
                strengths=list(
                    weekly_debrief
                    .debrief.strengths
                ),
                warnings=list(
                    weekly_debrief
                    .debrief.warnings
                ),
                planned_sessions=(
                    weekly_debrief
                    .facts.planned_sessions
                ),
                completed_sessions=(
                    weekly_debrief
                    .facts.completed_sessions
                ),
                skipped_sessions=(
                    weekly_debrief
                    .facts.skipped_sessions
                ),
                supplementary_sessions=(
                    weekly_debrief
                    .facts.supplementary_sessions
                ),
                planned_duration_minutes=(
                    weekly_debrief
                    .facts.planned_duration_minutes
                ),
                actual_duration_minutes=(
                    weekly_debrief
                    .facts.actual_duration_minutes
                ),
                planned_load=(
                    weekly_debrief
                    .facts.planned_load
                ),
                actual_load=(
                    weekly_debrief
                    .facts.actual_load
                ),
            )
            if weekly_debrief is not None
            else None
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
        recovery=recovery_payload,
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
