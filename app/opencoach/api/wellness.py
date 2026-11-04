from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
)
from opencoach.database.repositories import (
    SqlWellnessRepository,
    WellnessRepositoryError,
)
from opencoach.database.session import get_db
from opencoach.models import WellnessDay
from opencoach.wellness_trends import (
    WellnessMetricTrend,
    WellnessTrends,
    build_wellness_trends,
)


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
        get_current_athlete_profile_id,
    ),
    repository: SqlWellnessRepository = Depends(
        get_wellness_repository,
    ),
) -> WellnessDay:
    try:
        coros_latest = repository.get_latest(
            athlete_profile_id,
            provider="coros",
        )
        intervals_latest = repository.get_latest(
            athlete_profile_id,
            provider="intervals",
        )
        available = [
            item for item in (coros_latest, intervals_latest)
            if item is not None
        ]
        wellness = max(
            available,
            key=lambda item: (item.date, item.provider == "coros"),
            default=None,
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

@router.get("/trends")
def get_wellness_trends(
    days: int = 7,
    provider: str = "coros",
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    repository: SqlWellnessRepository = Depends(
        get_wellness_repository,
    ),
) -> dict:
    """Retourne les tendances Wellness récentes."""

    if provider not in {"coros", "intervals"}:
        raise HTTPException(
            status_code=422,
            detail="Le fournisseur doit être coros ou intervals.",
        )

    if not 2 <= days <= 30:
        raise HTTPException(
            status_code=422,
            detail=(
                "La fenêtre doit être comprise "
                "entre 2 et 30 jours."
            ),
        )

    end_date = date.today()

    start_date = (
        end_date
        - timedelta(
            days=days - 1
        )
    )

    try:
        wellness_days = (
            repository.list_range(
                athlete_profile_id,
                start_date,
                end_date,
                provider=provider,
            )
        )
        if not wellness_days and provider == "coros":
            wellness_days = repository.list_range(
                athlete_profile_id,
                start_date,
                end_date,
                provider="intervals",
            )
            if wellness_days:
                provider = "intervals"

    except WellnessRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger "
                "les tendances Wellness."
            ),
        ) from exc

    trends = build_wellness_trends(
        wellness_days=wellness_days,
        start_date=start_date,
        end_date=end_date,
        days=days,
    )

    return _trends_response(trends, provider=provider)


def _trends_response(
    trends: WellnessTrends,
    *,
    provider: str,
) -> dict:
    return {
        "provider": provider,
        "start_date": (
            trends.start_date.isoformat()
        ),
        "end_date": (
            trends.end_date.isoformat()
        ),
        "days": trends.days,
        "metrics": {
            "hrv": _metric_trend_response(trends.hrv),
            "hrv_baseline": _metric_trend_response(trends.hrv_baseline),
            "resting_hr": _metric_trend_response(trends.resting_hr),
            "stress_avg": _metric_trend_response(trends.stress_avg),
            "sleep_score": _metric_trend_response(
                trends.sleep_score
            ),
            "sleep_seconds": _metric_trend_response(trends.sleep_seconds),
            "sleep_deep_seconds": _metric_trend_response(trends.sleep_deep_seconds),
            "sleep_light_seconds": _metric_trend_response(trends.sleep_light_seconds),
            "sleep_rem_seconds": _metric_trend_response(trends.sleep_rem_seconds),
            "sleep_awake_seconds": _metric_trend_response(trends.sleep_awake_seconds),
            "fitness_ctl": _metric_trend_response(
                trends.fitness_ctl
            ),
            "fatigue_atl": _metric_trend_response(
                trends.fatigue_atl
            ),
        },
    }


def _metric_trend_response(
    trend: WellnessMetricTrend,
) -> dict:
    return {
        "current": trend.current,
        "average": trend.average,
        "change_percent": (
            trend.change_percent
        ),
        "direction": (
            trend.direction
        ),
        "sample_count": (
            trend.sample_count
        ),
        "points": [
            {
                "date": (
                    point.date.isoformat()
                ),
                "value": point.value,
            }
            for point in trend.points
        ],
    }
