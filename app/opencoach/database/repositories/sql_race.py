from datetime import (
    date,
    datetime,
    time,
)
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    Activity as ActivityModel,
    Race as RaceModel,
)
from opencoach.database.repositories.errors import (
    RaceRepositoryError,
)
from opencoach.database.repositories.race import (
    RaceRepository,
)
from opencoach.models import (
    Activity,
    Race,
)

class SqlRaceRepository(
    RaceRepository,
):
    """Persiste les courses dans la base SQL."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_race(
        self,
        athlete_profile_id: UUID,
        race: Race,
    ) -> Race:
        """Crée ou met à jour une course."""

        try:
            if race.id is None:
                database_race = RaceModel(
                    athlete_profile_id=athlete_profile_id,
                )

                self.session.add(
                    database_race
                )

            else:
                database_race = self.session.scalar(
                    select(RaceModel).where(
                        RaceModel.id == race.id,
                        RaceModel.athlete_profile_id
                        == athlete_profile_id,
                    )
                )

                if database_race is None:
                    raise RaceRepositoryError(
                        "Course introuvable."
                    )

            database_race.date = race.date
            database_race.name = race.name
            database_race.location = race.location
            database_race.race_type = race.race_type
            database_race.priority = race.priority

            database_race.distance_km = (
                race.distance_km
            )
            database_race.elevation_gain_m = (
                race.elevation_gain_m
            )
            database_race.target_time_minutes = (
                race.target_time_minutes
            )

            database_race.status = race.status

            database_race.actual_distance_km = (
                race.actual_distance_km
            )
            database_race.actual_elevation_gain_m = (
                race.actual_elevation_gain_m
            )
            database_race.actual_time_minutes = (
                race.actual_time_minutes
            )

            database_race.ranking = race.ranking
            database_race.notes = race.notes
            database_race.activity_id = race.activity_id

            self.session.commit()
            self.session.refresh(
                database_race
            )

            return self._to_domain(
                database_race
            )

        except RaceRepositoryError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                "Impossible d'enregistrer la course."
            ) from exc

    def get_race(
        self,
        athlete_profile_id: UUID,
        race_id: UUID,
    ) -> Race | None:
        """Retourne une course par identifiant."""

        try:
            database_race = self.session.scalar(
                select(RaceModel).where(
                    RaceModel.id == race_id,
                    RaceModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_race is None:
                return None

            return self._to_domain(
                database_race
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                "Impossible de charger la course."
            ) from exc

    def delete_race(
        self,
        athlete_profile_id: UUID,
        race_id: UUID,
    ) -> None:
        """Supprime une course."""

        try:
            database_race = self.session.scalar(
                select(RaceModel).where(
                    RaceModel.id == race_id,
                    RaceModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_race is None:
                raise RaceRepositoryError(
                    "Course introuvable."
                )

            self.session.delete(
                database_race
            )
            self.session.commit()

        except RaceRepositoryError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                "Impossible de supprimer la course."
            ) from exc

    def list_races_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Race]:
        """Retourne les courses d'une période."""

        try:
            statement = (
                select(RaceModel)
                .where(
                    RaceModel.athlete_profile_id
                    == athlete_profile_id,
                    RaceModel.date >= start_date,
                    RaceModel.date <= end_date,
                )
                .order_by(
                    RaceModel.date.asc(),
                    RaceModel.id.asc(),
                )
            )

            database_races = self.session.scalars(
                statement
            ).all()

            return [
                self._to_domain(
                    database_race
                )
                for database_race
                in database_races
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                "Impossible de charger les courses."
            ) from exc

    def list_upcoming_races(
        self,
        athlete_profile_id: UUID,
        from_date: date,
    ) -> list[Race]:
        """Retourne les courses planifiées à venir."""

        try:
            statement = (
                select(RaceModel)
                .where(
                    RaceModel.athlete_profile_id
                    == athlete_profile_id,
                    RaceModel.date >= from_date,
                    RaceModel.status == "planned",
                )
                .order_by(
                    RaceModel.date.asc(),
                    RaceModel.id.asc(),
                )
            )

            database_races = self.session.scalars(
                statement
            ).all()

            return [
                self._to_domain(
                    database_race
                )
                for database_race
                in database_races
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                (
                    "Impossible de charger "
                    "les prochaines courses."
                )
            ) from exc

    def get_next_primary_race(
        self,
        athlete_profile_id: UUID,
        from_date: date,
    ) -> Race | None:
        """Retourne le prochain objectif prioritaire."""

        try:
            statement = (
                select(RaceModel)
                .where(
                    RaceModel.athlete_profile_id
                    == athlete_profile_id,
                    RaceModel.date >= from_date,
                    RaceModel.status == "planned",
                    RaceModel.priority == "primary",
                )
                .order_by(
                    RaceModel.date.asc(),
                    RaceModel.id.asc(),
                )
                .limit(1)
            )

            database_race = self.session.scalar(
                statement
            )

            if database_race is None:
                return None

            return self._to_domain(
                database_race
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                (
                    "Impossible de charger "
                    "le prochain objectif prioritaire."
                )
            ) from exc

    def list_training_races_before(
        self,
        athlete_profile_id: UUID,
        from_date: date,
        primary_date: date,
    ) -> list[Race]:
        """Retourne les courses d'entraînement avant l'objectif."""

        try:
            statement = (
                select(RaceModel)
                .where(
                    RaceModel.athlete_profile_id
                    == athlete_profile_id,
                    RaceModel.date >= from_date,
                    RaceModel.date < primary_date,
                    RaceModel.status == "planned",
                    RaceModel.priority == "training",
                )
                .order_by(
                    RaceModel.date.asc(),
                    RaceModel.id.asc(),
                )
            )

            database_races = self.session.scalars(
                statement
            ).all()

            return [
                self._to_domain(
                    database_race
                )
                for database_race
                in database_races
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                (
                    "Impossible de charger les courses "
                    "d'entraînement de la préparation."
                )
            ) from exc

    def link_activity(
        self,
        athlete_profile_id: UUID,
        race_id: UUID,
        activity_id: UUID | None,
    ) -> Race:
        """Associe ou désassocie une activité à une course."""

        database_race = self._get_required_race(
            athlete_profile_id,
            race_id,
        )

        try:
            if activity_id is not None:
                activity = self.session.scalar(
                    select(ActivityModel).where(
                        ActivityModel.id == activity_id,
                        ActivityModel.athlete_profile_id
                        == athlete_profile_id,
                    )
                )

                if activity is None:
                    raise RaceRepositoryError(
                        "Activité introuvable."
                    )

            database_race.activity_id = activity_id

            self.session.commit()
            self.session.refresh(
                database_race
            )

            return self._to_domain(
                database_race
            )

        except RaceRepositoryError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                (
                    "Impossible d'associer "
                    "l'activité à la course."
                )
            ) from exc

    def list_candidate_activities_for_date(
        self,
        athlete_profile_id: UUID,
        race_date: date,
    ) -> list[Activity]:
        """Retourne les activités réalisées le jour de la course."""

        start_datetime = datetime.combine(
            race_date,
            time.min,
        )

        end_datetime = datetime.combine(
            race_date,
            time.max,
        )

        try:
            statement = (
                select(ActivityModel)
                .where(
                    ActivityModel.athlete_profile_id
                    == athlete_profile_id,
                    ActivityModel.start_at_local.is_not(
                        None
                    ),
                    ActivityModel.start_at_local
                    >= start_datetime,
                    ActivityModel.start_at_local
                    <= end_datetime,
                )
                .order_by(
                    ActivityModel.start_at_local.asc()
                )
            )

            activities = self.session.scalars(
                statement
            ).all()

            return [
                self._activity_to_domain(
                    activity
                )
                for activity in activities
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise RaceRepositoryError(
                (
                    "Impossible de rechercher "
                    "les activités du jour de la course."
                )
            ) from exc

    def _get_required_race(
        self,
        athlete_profile_id: UUID,
        race_id: UUID,
    ) -> RaceModel:
        database_race = self.session.scalar(
            select(RaceModel).where(
                RaceModel.id == race_id,
                RaceModel.athlete_profile_id
                == athlete_profile_id,
            )
        )

        if database_race is None:
            raise RaceRepositoryError(
                "Course introuvable."
            )

        return database_race

    @staticmethod
    def _to_domain(
        race: RaceModel,
    ) -> Race:
        return Race(
            id=race.id,
            date=race.date,
            name=race.name,
            location=race.location,
            race_type=race.race_type,
            priority=race.priority,
            distance_km=race.distance_km,
            elevation_gain_m=race.elevation_gain_m,
            target_time_minutes=(
                race.target_time_minutes
            ),
            status=race.status,
            actual_distance_km=(
                race.actual_distance_km
            ),
            actual_elevation_gain_m=(
                race.actual_elevation_gain_m
            ),
            actual_time_minutes=(
                race.actual_time_minutes
            ),
            ranking=race.ranking,
            notes=race.notes,
            activity_id=race.activity_id,
        )

    @staticmethod
    def _activity_to_domain(
        activity: ActivityModel,
    ) -> Activity:
        return Activity(
            provider=activity.provider,
            provider_activity_id=(
                activity.provider_activity_id
            ),
            source=activity.source,
            source_file_name=(
                activity.source_file_name
            ),
            name=activity.name,
            sport_type=activity.sport_type,
            start_at=activity.start_at,
            start_at_local=(
                activity.start_at_local
            ),
            device_name=activity.device_name,
            elapsed_time_seconds=(
                activity.elapsed_time_seconds
            ),
            moving_time_seconds=(
                activity.moving_time_seconds
            ),
            distance_m=activity.distance_m,
            elevation_gain_m=(
                activity.elevation_gain_m
            ),
            elevation_loss_m=(
                activity.elevation_loss_m
            ),
            average_speed_mps=(
                activity.average_speed_mps
            ),
            max_speed_mps=(
                activity.max_speed_mps
            ),
            average_heart_rate=(
                activity.average_heart_rate
            ),
            max_heart_rate=(
                activity.max_heart_rate
            ),
            lactate_threshold_heart_rate=(
                activity.lactate_threshold_heart_rate
            ),
            athlete_max_heart_rate=(
                activity.athlete_max_heart_rate
            ),
            average_cadence=(
                activity.average_cadence
            ),
            average_stride_m=(
                activity.average_stride_m
            ),
            average_stance_time_ms=(
                activity.average_stance_time_ms
            ),
            average_vertical_oscillation_mm=(
                activity.average_vertical_oscillation_mm
            ),
            average_power_w=(
                activity.average_power_w
            ),
            average_altitude_m=(
                activity.average_altitude_m
            ),
            min_altitude_m=(
                activity.min_altitude_m
            ),
            max_altitude_m=(
                activity.max_altitude_m
            ),
            average_temperature_c=(
                activity.average_temperature_c
            ),
            min_temperature_c=(
                activity.min_temperature_c
            ),
            max_temperature_c=(
                activity.max_temperature_c
            ),
            calories=activity.calories,
            training_load=(
                activity.training_load
            ),
            fitness_ctl=activity.fitness_ctl,
            fatigue_atl=activity.fatigue_atl,
            hr_load=activity.hr_load,
            intensity=activity.intensity,
            feel=activity.feel,
            id=activity.id,
        )
