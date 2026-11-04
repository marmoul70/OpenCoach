"""Lecture des snapshots COROS normalisés en séries temporelles."""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import CorosDailyData


class CorosDailyDataRepositoryError(RuntimeError):
    """Erreur de lecture des snapshots COROS."""


class SqlCorosDailyDataRepository:
    """Accède aux snapshots COROS sans dupliquer leur stockage."""

    TIME_SERIES_CATEGORIES = (
        "hrv_timeseries",
        "stress_points",
        "health_check_points",
    )

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_time_series_snapshots(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Retourne les snapshots de séries d'une période, du plus ancien au plus récent."""
        if start_date > end_date:
            raise ValueError("start_date doit être antérieure ou égale à end_date.")

        try:
            rows = self.session.scalars(
                select(CorosDailyData)
                .where(
                    CorosDailyData.athlete_profile_id == athlete_profile_id,
                    CorosDailyData.metric_date >= start_date,
                    CorosDailyData.metric_date <= end_date,
                    CorosDailyData.category.in_(self.TIME_SERIES_CATEGORIES),
                )
                .order_by(CorosDailyData.metric_date.asc(), CorosDailyData.category.asc())
            ).all()
            return [
                {
                    "metric_date": row.metric_date,
                    "category": row.category,
                    "payload": row.payload,
                }
                for row in rows
            ]
        except SQLAlchemyError as exc:
            raise CorosDailyDataRepositoryError(
                "Impossible de charger les séries temporelles COROS."
            ) from exc
