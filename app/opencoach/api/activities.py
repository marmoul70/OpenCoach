from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
)
from opencoach.database.repositories import (
    ActivityRepositoryError,
    SqlActivityRepository,
)
from opencoach.database.session import get_db
from opencoach.models import Activity


router = APIRouter(
    prefix="/api/activities",
    tags=["activities"],
)


def get_activity_repository(
    db: Session = Depends(get_db),
) -> SqlActivityRepository:
    return SqlActivityRepository(db)


@router.get("")
def list_activities(
    athlete_profile_id: UUID = Depends(
        get_current_athlete_profile_id,
    ),
    repository: SqlActivityRepository = Depends(
        get_activity_repository,
    ),
) -> list[Activity]:
    try:
        return repository.list_activities(
            athlete_profile_id,
        )
    except ActivityRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de charger les activités.",
        ) from exc


@router.get("/{activity_id}/detail")
def get_activity_detail(
    activity_id: UUID,
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict:
    """Retourne la fiche activité et le détail COROS conservé à l'import."""
    from datetime import timedelta

    from sqlalchemy import select

    from opencoach.database.models import Activity as ActivityModel
    from opencoach.database.models import CorosDailyData

    activity = db.scalar(
        select(ActivityModel).where(
            ActivityModel.id == activity_id,
            ActivityModel.athlete_profile_id == athlete_profile_id,
        )
    )
    if activity is None:
        raise HTTPException(status_code=404, detail="Activité introuvable.")

    response = {
        "id": str(activity.id),
        "provider": activity.provider,
        "provider_activity_id": activity.provider_activity_id,
        "name": activity.name,
        "sport_type": activity.sport_type,
        "start_at": activity.start_at.isoformat(),
        "start_at_local": activity.start_at_local.isoformat() if activity.start_at_local else None,
        "distance_m": activity.distance_m,
        "elapsed_time_seconds": activity.elapsed_time_seconds,
        "moving_time_seconds": activity.moving_time_seconds,
        "elevation_gain_m": activity.elevation_gain_m,
        "elevation_loss_m": activity.elevation_loss_m,
        "average_heart_rate": activity.average_heart_rate,
        "max_heart_rate": activity.max_heart_rate,
        "average_speed_mps": activity.average_speed_mps,
        "average_power_w": activity.average_power_w,
        "average_cadence": activity.average_cadence,
        "average_stride_m": activity.average_stride_m,
        "calories": activity.calories,
        "training_load": activity.training_load,
        "coros_detail": None,
        "coros_record": None,
    }

    if activity.provider != "coros":
        return response

    activity_date = activity.start_at.date()
    snapshots = db.scalars(
        select(CorosDailyData).where(
            CorosDailyData.athlete_profile_id == athlete_profile_id,
            CorosDailyData.category == "activities",
            CorosDailyData.metric_date >= activity_date - timedelta(days=1),
            CorosDailyData.metric_date <= activity_date + timedelta(days=1),
        )
    ).all()

    for snapshot in snapshots:
        payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
        records = payload.get("activities")
        if not isinstance(records, list):
            records = [payload] if payload else []
        for record in records:
            if not isinstance(record, dict):
                continue
            label_id = record.get("labelId") or record.get("label_id")
            if str(label_id) != activity.provider_activity_id:
                continue
            response["coros_record"] = record
            response["coros_detail"] = record.get("activity_detail")
            return response

    return response


@router.get("/provider/{provider}/{provider_activity_id}/detail")
def get_activity_detail_by_provider_id(
    provider: str,
    provider_activity_id: str,
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict:
    """Retourne le détail d'une activité via son identifiant fournisseur, sans dépendre d'une séance Coach."""
    from datetime import timedelta

    from sqlalchemy import select

    from opencoach.database.models import Activity as ActivityModel
    from opencoach.database.models import CorosDailyData

    activity = db.scalar(
        select(ActivityModel).where(
            ActivityModel.provider == provider,
            ActivityModel.provider_activity_id == provider_activity_id,
            ActivityModel.athlete_profile_id == athlete_profile_id,
        )
    )
    if activity is None:
        raise HTTPException(status_code=404, detail="Activité introuvable.")

    response = {
        "id": str(activity.id),
        "provider": activity.provider,
        "provider_activity_id": activity.provider_activity_id,
        "name": activity.name,
        "sport_type": activity.sport_type,
        "start_at": activity.start_at.isoformat(),
        "start_at_local": activity.start_at_local.isoformat() if activity.start_at_local else None,
        "distance_m": activity.distance_m,
        "elapsed_time_seconds": activity.elapsed_time_seconds,
        "moving_time_seconds": activity.moving_time_seconds,
        "elevation_gain_m": activity.elevation_gain_m,
        "elevation_loss_m": activity.elevation_loss_m,
        "average_heart_rate": activity.average_heart_rate,
        "max_heart_rate": activity.max_heart_rate,
        "average_speed_mps": activity.average_speed_mps,
        "average_power_w": activity.average_power_w,
        "average_cadence": activity.average_cadence,
        "average_stride_m": activity.average_stride_m,
        "calories": activity.calories,
        "training_load": activity.training_load,
        "coros_detail": None,
        "coros_record": None,
    }

    if provider != "coros":
        return response

    activity_date = activity.start_at.date()
    snapshots = db.scalars(
        select(CorosDailyData).where(
            CorosDailyData.athlete_profile_id == athlete_profile_id,
            CorosDailyData.category == "activities",
            CorosDailyData.metric_date >= activity_date - timedelta(days=1),
            CorosDailyData.metric_date <= activity_date + timedelta(days=1),
        )
    ).all()

    for snapshot in snapshots:
        payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
        records = payload.get("activities")
        if not isinstance(records, list):
            records = [payload] if payload else []
        for record in records:
            if not isinstance(record, dict):
                continue
            label_id = record.get("labelId") or record.get("label_id")
            if str(label_id) != provider_activity_id:
                continue
            response["coros_record"] = record
            response["coros_detail"] = record.get("activity_detail")
            return response

    return response
