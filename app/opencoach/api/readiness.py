from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
)
from opencoach.database.repositories import (
    DailyContextRepositoryError,
    SqlDailyContextRepository,
    SqlWellnessRepository,
    WellnessRepositoryError,
)
from opencoach.database.session import get_db
from opencoach.readiness import (
    ReadinessAssessment,
    ReadinessDataUnavailableError,
    ReadinessService,
)
from opencoach.schemas.readiness import (
    DailyReadinessResponse,
    MetricBaselineResponse,
    MetricComparisonResponse,
    ReadinessAssessmentResponse,
    ReadinessBaselineResponse,
    ReadinessComparisonResponse,
    ReadinessSignalResponse,
)


router = APIRouter(
    prefix="/api/readiness",
    tags=["readiness"],
)


def get_readiness_service(
    db: Session = Depends(get_db),
) -> ReadinessService:
    wellness_repository = SqlWellnessRepository(
        db
    )

    daily_context_repository = (
        SqlDailyContextRepository(
            db
        )
    )

    return ReadinessService(
        wellness_repository,
        daily_context_repository=(
            daily_context_repository
        ),
        provider="intervals",
    )


@router.get(
    "/today",
    response_model=ReadinessAssessmentResponse,
)
def get_today_readiness(
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    service: ReadinessService = Depends(
        get_readiness_service,
    ),
) -> ReadinessAssessmentResponse:
    try:
        assessment = service.calculate(
            athlete_profile_id,
            date.today(),
        )

    except ReadinessDataUnavailableError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except (
        WellnessRepositoryError,
        DailyContextRepositoryError,
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger les données "
                "nécessaires au Readiness."
            ),
        ) from exc
    return _to_response(
        assessment,
    )


def _to_response(
    assessment: ReadinessAssessment,
) -> ReadinessAssessmentResponse:
    return ReadinessAssessmentResponse(
        date=assessment.date,
        provider=assessment.provider,

        baseline=ReadinessBaselineResponse(
            start_date=assessment.baseline.start_date,
            end_date=assessment.baseline.end_date,

            hrv=_baseline_metric_response(
                assessment.baseline.hrv,
            ),
            resting_hr=_baseline_metric_response(
                assessment.baseline.resting_hr,
            ),
            sleep_seconds=_baseline_metric_response(
                assessment.baseline.sleep_seconds,
            ),
            sleep_score=_baseline_metric_response(
                assessment.baseline.sleep_score,
            ),
        ),

        comparison=ReadinessComparisonResponse(
            hrv=_comparison_metric_response(
                assessment.comparison.hrv,
            ),
            resting_hr=_comparison_metric_response(
                assessment.comparison.resting_hr,
            ),
            sleep_seconds=_comparison_metric_response(
                assessment.comparison.sleep_seconds,
            ),
            sleep_score=_comparison_metric_response(
                assessment.comparison.sleep_score,
            ),
        ),

        readiness=DailyReadinessResponse(
            score=assessment.readiness.score,
            level=assessment.readiness.level,

            warning_count=(
                assessment.readiness.warning_count
            ),
            critical_count=(
                assessment.readiness.critical_count
            ),

            training_constraints=list(
                assessment.readiness.training_constraints
            ),

            fitness_ctl=assessment.readiness.fitness_ctl,
            fatigue_atl=assessment.readiness.fatigue_atl,
            training_balance=(
                assessment.readiness.training_balance
            ),

            signals=[
                ReadinessSignalResponse(
                    metric=signal.metric,
                    level=signal.level,
                    reason=signal.reason,
                    current_value=signal.current_value,
                    reference_value=signal.reference_value,
                )
                for signal in assessment.readiness.signals
            ],
        ),
    )


def _baseline_metric_response(
    metric,
) -> MetricBaselineResponse:
    return MetricBaselineResponse(
        median=metric.median,
        sample_count=metric.sample_count,
        reliable=metric.reliable,
    )


def _comparison_metric_response(
    metric,
) -> MetricComparisonResponse:
    return MetricComparisonResponse(
        current=metric.current,
        baseline=metric.baseline,
        absolute_delta=metric.absolute_delta,
        percent_delta=metric.percent_delta,
        reliable=metric.reliable,
    )
