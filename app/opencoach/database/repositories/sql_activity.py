from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, or_, select

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import Activity as ActivityModel
from opencoach.database.repositories.activity import (
    ActivityRepository,
)
from opencoach.database.repositories.errors import (
    ActivityRepositoryError,
)
from opencoach.models import Activity


class SqlActivityRepository(ActivityRepository):
    """Persiste les activités sportives dans la base SQL."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_activity(
        self,
        athlete_profile_id: UUID,
        activity: Activity,
    ) -> None:
        try:
            database_activity = self._get_database_activity(
                provider=activity.provider,
                provider_activity_id=(
                    activity.provider_activity_id
                ),
            )

            if database_activity is None:
                database_activity = ActivityModel(
                    athlete_profile_id=athlete_profile_id,
                    provider=activity.provider,
                    provider_activity_id=(
                        activity.provider_activity_id
                    ),
                )

                self.session.add(database_activity)

            database_activity.athlete_profile_id = (
                athlete_profile_id
            )

            database_activity.source = activity.source
            database_activity.source_file_name = (
                activity.source_file_name
            )

            database_activity.name = activity.name
            database_activity.sport_type = activity.sport_type

            database_activity.start_at = activity.start_at
            database_activity.start_at_local = (
                activity.start_at_local
            )

            database_activity.device_name = (
                activity.device_name
            )

            database_activity.elapsed_time_seconds = (
                activity.elapsed_time_seconds
            )
            database_activity.moving_time_seconds = (
                activity.moving_time_seconds
            )

            database_activity.distance_m = activity.distance_m
            database_activity.elevation_gain_m = (
                activity.elevation_gain_m
            )
            database_activity.elevation_loss_m = (
                activity.elevation_loss_m
            )

            database_activity.average_speed_mps = (
                activity.average_speed_mps
            )
            database_activity.max_speed_mps = (
                activity.max_speed_mps
            )

            database_activity.average_heart_rate = (
                activity.average_heart_rate
            )
            database_activity.max_heart_rate = (
                activity.max_heart_rate
            )
            database_activity.lactate_threshold_heart_rate = (
                activity.lactate_threshold_heart_rate
            )
            database_activity.athlete_max_heart_rate = (
                activity.athlete_max_heart_rate
            )

            database_activity.average_cadence = (
                activity.average_cadence
            )
            database_activity.average_stride_m = (
                activity.average_stride_m
            )
            database_activity.average_stance_time_ms = (
                activity.average_stance_time_ms
            )
            database_activity.average_vertical_oscillation_mm = (
                activity.average_vertical_oscillation_mm
            )
            database_activity.average_power_w = (
                activity.average_power_w
            )

            database_activity.average_altitude_m = (
                activity.average_altitude_m
            )
            database_activity.min_altitude_m = (
                activity.min_altitude_m
            )
            database_activity.max_altitude_m = (
                activity.max_altitude_m
            )

            database_activity.average_temperature_c = (
                activity.average_temperature_c
            )
            database_activity.min_temperature_c = (
                activity.min_temperature_c
            )
            database_activity.max_temperature_c = (
                activity.max_temperature_c
            )

            database_activity.calories = activity.calories

            database_activity.training_load = (
                activity.training_load
            )
            database_activity.fitness_ctl = (
                activity.fitness_ctl
            )
            database_activity.fatigue_atl = (
                activity.fatigue_atl
            )
            database_activity.hr_load = activity.hr_load
            database_activity.intensity = activity.intensity
            database_activity.feel = activity.feel

            self.session.commit()
            self.session.refresh(database_activity)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise ActivityRepositoryError(
                "Impossible d'enregistrer l'activité."
            ) from exc

    def get_activity(
        self,
        athlete_profile_id: UUID,
        activity_id: UUID,
    ) -> Activity | None:
        """Retourne une activité par identifiant."""

        try:
            database_activity = self.session.scalar(
                select(ActivityModel).where(
                    ActivityModel.id == activity_id,
                    ActivityModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_activity is None:
                return None

            return self._to_domain(
                database_activity
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise ActivityRepositoryError(
                "Impossible de charger l'activité."
            ) from exc

    def list_activities(
        self,
        athlete_profile_id: UUID,
    ) -> list[Activity]:
        """Retourne les activités d'un athlète, de la plus récente à la plus ancienne."""

        try:
            statement = (
                select(ActivityModel)
                .where(
                    ActivityModel.athlete_profile_id
                    == athlete_profile_id
                )
                .order_by(
                    ActivityModel.start_at.desc()
                )
            )

            database_activities = self.session.scalars(
                statement
            ).all()

            return [
                self._to_domain(activity)
                for activity in database_activities
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise ActivityRepositoryError(
                "Impossible de charger les activités."
            ) from exc

    def list_activities_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Activity]:
        """Retourne les activités comprises dans une période.

        La date locale de l'activité est utilisée en priorité.
        Lorsque celle-ci n'est pas disponible, ``start_at`` est
        utilisé comme solution de repli.
        """

        if end_date < start_date:
            return []

        start_datetime = datetime.combine(
            start_date,
            time.min,
        )

        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
        )

        try:
            statement = (
                select(ActivityModel)
                .where(
                    ActivityModel.athlete_profile_id
                    == athlete_profile_id,
                    or_(
                        and_(
                            ActivityModel.start_at_local
                            .is_not(None),
                            ActivityModel.start_at_local
                            >= start_datetime,
                            ActivityModel.start_at_local
                            < end_datetime,
                        ),
                        and_(
                            ActivityModel.start_at_local
                            .is_(None),
                            ActivityModel.start_at
                            >= start_datetime,
                            ActivityModel.start_at
                            < end_datetime,
                        ),
                    ),
                )
                .order_by(
                    ActivityModel.start_at.desc(),
                )
            )

            database_activities = (
                self.session.scalars(
                    statement,
                ).all()
            )

            return [
                self._to_domain(
                    activity,
                )
                for activity
                in database_activities
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise ActivityRepositoryError(
                (
                    "Impossible de charger les activités "
                    "de la période."
                )
            ) from exc

    def _get_database_activity(
        self,
        *,
        provider: str,
        provider_activity_id: str,
    ) -> ActivityModel | None:
        statement = (
            select(ActivityModel)
            .where(
                ActivityModel.provider == provider,
                ActivityModel.provider_activity_id
                == provider_activity_id,
            )
        )

        return self.session.scalar(statement)

    @staticmethod
    def _to_domain(
        activity: ActivityModel,
    ) -> Activity:
        return Activity(
            provider=activity.provider,
            provider_activity_id=activity.provider_activity_id,
            source=activity.source,
            source_file_name=activity.source_file_name,
            name=activity.name,
            sport_type=activity.sport_type,
            start_at=activity.start_at,
            start_at_local=activity.start_at_local,
            device_name=activity.device_name,
            elapsed_time_seconds=activity.elapsed_time_seconds,
            moving_time_seconds=activity.moving_time_seconds,
            distance_m=activity.distance_m,
            elevation_gain_m=activity.elevation_gain_m,
            elevation_loss_m=activity.elevation_loss_m,
            average_speed_mps=activity.average_speed_mps,
            max_speed_mps=activity.max_speed_mps,
            average_heart_rate=activity.average_heart_rate,
            max_heart_rate=activity.max_heart_rate,
            lactate_threshold_heart_rate=(
                activity.lactate_threshold_heart_rate
            ),
            athlete_max_heart_rate=activity.athlete_max_heart_rate,
            average_cadence=activity.average_cadence,
            average_stride_m=activity.average_stride_m,
            average_stance_time_ms=activity.average_stance_time_ms,
            average_vertical_oscillation_mm=(
                activity.average_vertical_oscillation_mm
            ),
            average_power_w=activity.average_power_w,
            average_altitude_m=activity.average_altitude_m,
            min_altitude_m=activity.min_altitude_m,
            max_altitude_m=activity.max_altitude_m,
            average_temperature_c=activity.average_temperature_c,
            min_temperature_c=activity.min_temperature_c,
            max_temperature_c=activity.max_temperature_c,
            calories=activity.calories,
            training_load=activity.training_load,
            fitness_ctl=activity.fitness_ctl,
            fatigue_atl=activity.fatigue_atl,
            hr_load=activity.hr_load,
            intensity=activity.intensity,
            feel=activity.feel,
            id=activity.id,
        )