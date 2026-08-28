"""Repository SQL des données détaillées d'activité."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    Activity as ActivityModel,
    ActivityDetail as ActivityDetailModel,
    ActivityInterval as ActivityIntervalModel,
    ActivityStream as ActivityStreamModel,
)
from opencoach.database.repositories.activity_detail import (
    ActivityDetailRepository,
)
from opencoach.database.repositories.errors import (
    ActivityRepositoryError,
)
from opencoach.models import (
    ActivityDetail,
    ActivityInterval,
    ActivityStream,
    ActivityStreams,
)


class SqlActivityDetailRepository(
    ActivityDetailRepository
):
    """Persiste les détails nécessaires au coach."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_activity_detail(
        self,
        athlete_profile_id: UUID,
        detail: ActivityDetail,
    ) -> None:
        try:
            activity = self.session.scalar(
                select(ActivityModel).where(
                    ActivityModel.athlete_profile_id
                    == athlete_profile_id,
                    ActivityModel.provider_activity_id
                    == detail.provider_activity_id,
                )
            )

            if activity is None:
                raise ActivityRepositoryError(
                    "L'activité associée au détail "
                    "est introuvable."
                )

            database_detail = self.session.get(
                ActivityDetailModel,
                activity.id,
            )

            if database_detail is None:
                database_detail = ActivityDetailModel(
                    activity_id=activity.id,
                )
                self.session.add(
                    database_detail
                )

            database_detail.provider_lap_count = (
                detail.provider_lap_count
            )

            database_detail.interval_summary = list(
                detail.interval_summary
            )

            self.session.flush()

            self.session.execute(
                delete(ActivityIntervalModel).where(
                    ActivityIntervalModel.activity_id
                    == activity.id
                )
            )

            self.session.execute(
                delete(ActivityStreamModel).where(
                    ActivityStreamModel.activity_id
                    == activity.id
                )
            )

            for position, interval in enumerate(
                detail.intervals
            ):
                self.session.add(
                    ActivityIntervalModel(
                        activity_id=activity.id,
                        position=position,
                        provider_interval_id=(
                            interval.provider_interval_id
                        ),
                        interval_type=(
                            interval.interval_type
                        ),
                        label=interval.label,
                        start_index=interval.start_index,
                        end_index=interval.end_index,
                        start_time_seconds=(
                            interval.start_time_seconds
                        ),
                        end_time_seconds=(
                            interval.end_time_seconds
                        ),
                        distance_m=interval.distance_m,
                        moving_time_seconds=(
                            interval.moving_time_seconds
                        ),
                        elapsed_time_seconds=(
                            interval.elapsed_time_seconds
                        ),
                        average_speed_mps=(
                            interval.average_speed_mps
                        ),
                        average_heart_rate=(
                            interval.average_heart_rate
                        ),
                        max_heart_rate=(
                            interval.max_heart_rate
                        ),
                        average_cadence=(
                            interval.average_cadence
                        ),
                        elevation_gain_m=(
                            interval.elevation_gain_m
                        ),
                        training_load=(
                            interval.training_load
                        ),
                    )
                )

            for stream in _iter_streams(
                detail.streams
            ):
                self.session.add(
                    ActivityStreamModel(
                        activity_id=activity.id,
                        stream_type=stream.stream_type,
                        data=list(stream.data),
                    )
                )

            self.session.commit()

        except ActivityRepositoryError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise ActivityRepositoryError(
                "Impossible d'enregistrer "
                "le détail de l'activité."
            ) from exc

    def get_activity_detail(
        self,
        athlete_profile_id: UUID,
        activity_id: UUID,
    ) -> ActivityDetail | None:
        try:
            activity = self.session.scalar(
                select(ActivityModel).where(
                    ActivityModel.id == activity_id,
                    ActivityModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if activity is None:
                return None

            database_detail = self.session.get(
                ActivityDetailModel,
                activity.id,
            )

            if database_detail is None:
                return None

            intervals = self.session.scalars(
                select(ActivityIntervalModel)
                .where(
                    ActivityIntervalModel.activity_id
                    == activity.id
                )
                .order_by(
                    ActivityIntervalModel.position
                )
            ).all()

            streams = self.session.scalars(
                select(ActivityStreamModel)
                .where(
                    ActivityStreamModel.activity_id
                    == activity.id
                )
            ).all()

            mapped_streams = {
                stream.stream_type: ActivityStream(
                    stream_type=stream.stream_type,
                    data=tuple(stream.data),
                )
                for stream in streams
            }

            return ActivityDetail(
                provider_activity_id=(
                    activity.provider_activity_id
                ),
                intervals=tuple(
                    _to_interval(interval)
                    for interval in intervals
                ),
                streams=ActivityStreams(
                    time=mapped_streams.get("time"),
                    distance=mapped_streams.get(
                        "distance"
                    ),
                    heartrate=mapped_streams.get(
                        "heartrate"
                    ),
                    velocity_smooth=mapped_streams.get(
                        "velocity_smooth"
                    ),
                    cadence=mapped_streams.get(
                        "cadence"
                    ),
                    watts=mapped_streams.get(
                        "watts"
                    ),
                ),
                interval_summary=tuple(
                    database_detail.interval_summary
                    or []
                ),
                provider_lap_count=(
                    database_detail.provider_lap_count
                ),
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise ActivityRepositoryError(
                "Impossible de charger "
                "le détail de l'activité."
            ) from exc


def _iter_streams(
    streams: ActivityStreams,
):
    for stream in (
        streams.time,
        streams.distance,
        streams.heartrate,
        streams.velocity_smooth,
        streams.cadence,
        streams.watts,
    ):
        if stream is not None:
            yield stream


def _to_interval(
    interval: ActivityIntervalModel,
) -> ActivityInterval:
    return ActivityInterval(
        provider_interval_id=(
            interval.provider_interval_id
        ),
        interval_type=interval.interval_type,
        label=interval.label,
        start_index=interval.start_index,
        end_index=interval.end_index,
        start_time_seconds=(
            interval.start_time_seconds
        ),
        end_time_seconds=(
            interval.end_time_seconds
        ),
        distance_m=interval.distance_m,
        moving_time_seconds=(
            interval.moving_time_seconds
        ),
        elapsed_time_seconds=(
            interval.elapsed_time_seconds
        ),
        average_speed_mps=(
            interval.average_speed_mps
        ),
        average_heart_rate=(
            interval.average_heart_rate
        ),
        max_heart_rate=interval.max_heart_rate,
        average_cadence=(
            interval.average_cadence
        ),
        elevation_gain_m=(
            interval.elevation_gain_m
        ),
        training_load=interval.training_load,
    )
