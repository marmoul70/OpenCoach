from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    Activity as ActivityModel,
)
from opencoach.database.models import (
    TrainingSession as TrainingSessionModel,
)
from opencoach.database.repositories.errors import (
    TrainingSessionRepositoryError,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import Activity, TrainingSession


class SqlTrainingSessionRepository(
    TrainingSessionRepository,
):
    """Persiste les séances d'entraînement dans la base SQL."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_session(
        self,
        athlete_profile_id: UUID,
        session: TrainingSession,
    ) -> TrainingSession:
        """Crée ou met à jour une séance."""

        try:
            database_session = None

            if session.id is not None:
                database_session = self.session.scalar(
                    select(TrainingSessionModel).where(
                        TrainingSessionModel.id == session.id,
                        TrainingSessionModel.athlete_profile_id
                        == athlete_profile_id,
                    )
                )

            if database_session is None:
                database_session = TrainingSessionModel(
                    athlete_profile_id=athlete_profile_id,
                )

                self.session.add(database_session)

            database_session.date = session.date

            database_session.planning_key = (
                session.planning_key
            )
            database_session.planning_importance = (
                session.planning_importance
            )

            database_session.type = session.type
            database_session.title = session.title
            database_session.sport_type = session.sport_type
            database_session.description = session.description
            database_session.duration_minutes = (
                session.duration_minutes
            )
            database_session.distance_km = session.distance_km
            database_session.elevation_gain_m = (
                session.elevation_gain_m
            )
            database_session.intensity = session.intensity
            database_session.heart_rate_zone = (
                session.heart_rate_zone
            )
            database_session.prescription = (
                session.prescription
            )
            database_session.status = session.status
            database_session.activity_id = session.activity_id

            database_session.intervals_external_id = (
                session.intervals_external_id
            )
            database_session.intervals_event_id = (
                session.intervals_event_id
            )
            database_session.intervals_sync_status = (
                session.intervals_sync_status
            )
            database_session.intervals_last_synced_at = (
                session.intervals_last_synced_at
            )
            database_session.intervals_payload_hash = (
                session.intervals_payload_hash
            )
            database_session.intervals_sync_error = (
                session.intervals_sync_error
            )
            # Les objets de séance reconstruits par le planificateur ne
            # transportent pas les métadonnées COROS. Une absence dans un
            # objet métier ordinaire ne doit jamais effacer une identité
            # distante ; seules les valeurs explicitement fournies les
            # remplacent. Les transitions de synchronisation continuent
            # d'être écrites par le service COROS, qui relit l'objet courant.
            if (
                session.coros_workout_id is not None
                or database_session.coros_workout_id is None
            ):
                database_session.coros_workout_id = session.coros_workout_id
            if (
                session.coros_scheduled_date is not None
                or database_session.coros_workout_id is None
            ):
                database_session.coros_scheduled_date = session.coros_scheduled_date
            if (
                session.coros_sync_status is not None
                or database_session.coros_workout_id is None
            ):
                database_session.coros_sync_status = session.coros_sync_status
            if (
                session.coros_sync_started_at is not None
                or database_session.coros_workout_id is None
            ):
                database_session.coros_sync_started_at = session.coros_sync_started_at
            if (
                session.coros_last_synced_at is not None
                or database_session.coros_workout_id is None
            ):
                database_session.coros_last_synced_at = session.coros_last_synced_at
            if (
                session.coros_payload_hash is not None
                or database_session.coros_workout_id is None
            ):
                database_session.coros_payload_hash = session.coros_payload_hash
            if (
                session.coros_sync_error is not None
                or database_session.coros_workout_id is None
            ):
                database_session.coros_sync_error = session.coros_sync_error
            self.session.commit()
            self.session.refresh(database_session)

            return self._to_domain(database_session)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise TrainingSessionRepositoryError(
                "Impossible d'enregistrer la séance."
            ) from exc

    def claim_coros_workout_push(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        payload_hash: str,
        started_at: datetime,
        *,
        allow_uncertain: bool = False,
        allow_synced_update: bool = False,
    ) -> bool:
        """Réserve atomiquement une création ou la mise à jour d'une copie COROS."""
        started_at_utc = (
            started_at.replace(tzinfo=None)
            if started_at.tzinfo is not None
            else started_at
        )
        eligible_statuses = [
            TrainingSessionModel.coros_sync_status.is_(None),
            TrainingSessionModel.coros_sync_status == "failed",
        ]
        if allow_synced_update:
            eligible_statuses.append(
                and_(
                    TrainingSessionModel.coros_sync_status == "synced",
                    TrainingSessionModel.coros_workout_id.is_not(None),
                    TrainingSessionModel.coros_payload_hash != payload_hash,
                )
            )
        if allow_uncertain:
            stale_before = started_at_utc - timedelta(minutes=5)
            eligible_statuses.extend([
                TrainingSessionModel.coros_sync_status == "unknown",
                and_(
                    TrainingSessionModel.coros_sync_status == "pending",
                    or_(
                        TrainingSessionModel.coros_sync_started_at.is_(None),
                        TrainingSessionModel.coros_sync_started_at <= stale_before,
                    ),
                ),
            ])

        try:
            result = self.session.execute(
                update(TrainingSessionModel)
                .where(
                    TrainingSessionModel.id == session_id,
                    TrainingSessionModel.athlete_profile_id
                    == athlete_profile_id,
                    or_(*eligible_statuses),
                )
                .values(
                    coros_sync_status="pending",
                    coros_sync_started_at=started_at_utc,
                    coros_payload_hash=payload_hash,
                    coros_sync_error=None,
                )
                .execution_options(synchronize_session=False)
            )
            self.session.commit()
            return result.rowcount == 1
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise TrainingSessionRepositoryError(
                "Impossible de réserver l'envoi COROS."
            ) from exc

    def delete_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> None:
        """Supprime une séance appartenant à l'athlète."""

        database_session = (
            self.session.scalar(
                select(
                    TrainingSessionModel
                ).where(
                    TrainingSessionModel.id
                    == session_id,
                    TrainingSessionModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )
        )

        if database_session is None:
            raise TrainingSessionRepositoryError(
                "Séance introuvable."
            )

        # Ne jamais supprimer une référence distante sans suppression COROS
        # confirmée. La fonction de suppression distante sera distincte.
        if (
            database_session.coros_workout_id is not None
            or database_session.coros_sync_status in {
                "pending",
                "synced",
                "unknown",
            }
        ):
            raise TrainingSessionRepositoryError(
                "Une séance liée au calendrier COROS ne peut pas être supprimée automatiquement."
            )

        try:
            self.session.delete(
                database_session
            )
            self.session.commit()

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise TrainingSessionRepositoryError(
                "Impossible de supprimer la séance."
            ) from exc

    def get_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> TrainingSession | None:
        """Retourne une séance par identifiant."""

        try:
            database_session = self.session.scalar(
                select(TrainingSessionModel).where(
                    TrainingSessionModel.id == session_id,
                    TrainingSessionModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_session is None:
                return None

            return self._to_domain(database_session)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise TrainingSessionRepositoryError(
                "Impossible de charger la séance."
            ) from exc

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TrainingSession]:
        """Retourne les séances comprises dans une période."""

        try:
            statement = (
                select(TrainingSessionModel)
                .where(
                    TrainingSessionModel.athlete_profile_id
                    == athlete_profile_id,
                    TrainingSessionModel.date >= start_date,
                    TrainingSessionModel.date <= end_date,
                )
                .order_by(
                    TrainingSessionModel.date.asc(),
                    TrainingSessionModel.id.asc(),
                )
            )

            database_sessions = self.session.scalars(
                statement
            ).all()

            return [
                self._to_domain(database_session)
                for database_session in database_sessions
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise TrainingSessionRepositoryError(
                "Impossible de charger les séances."
            ) from exc

    def update_status(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        status: str,
    ) -> TrainingSession:
        """Met à jour le statut d'une séance."""

        database_session = self._get_required_session(
            athlete_profile_id,
            session_id,
        )

        try:
            database_session.status = status

            self.session.commit()
            self.session.refresh(database_session)

            return self._to_domain(database_session)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise TrainingSessionRepositoryError(
                "Impossible de modifier le statut de la séance."
            ) from exc

    def link_activity(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        activity_id: UUID | None,
    ) -> TrainingSession:
        """Associe ou désassocie une activité."""

        database_session = self._get_required_session(
            athlete_profile_id,
            session_id,
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
                    raise TrainingSessionRepositoryError(
                        "Activité introuvable."
                    )

            database_session.activity_id = activity_id

            self.session.commit()
            self.session.refresh(database_session)

            return self._to_domain(database_session)

        except TrainingSessionRepositoryError:
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise TrainingSessionRepositoryError(
                "Impossible d'associer l'activité à la séance."
            ) from exc

    def list_candidate_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        """Retourne les activités réalisées le même jour."""

        start_datetime = datetime.combine(
            session_date,
            time.min,
        )

        end_datetime = datetime.combine(
            session_date,
            time.max,
        )

        try:
            statement = (
                select(ActivityModel)
                .where(
                    ActivityModel.athlete_profile_id
                    == athlete_profile_id,
                    ActivityModel.start_at_local.is_not(None),
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
                self._activity_to_domain(activity)
                for activity in activities
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise TrainingSessionRepositoryError(
                "Impossible de rechercher les activités du jour."
            ) from exc

    def list_unlinked_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        """Retourne les activités du jour non liées à une séance."""

        start_datetime = datetime.combine(
            session_date,
            time.min,
        )

        end_datetime = datetime.combine(
            session_date,
            time.max,
        )

        try:
            linked_activity_ids = (
                select(
                    TrainingSessionModel.activity_id
                )
                .where(
                    TrainingSessionModel.athlete_profile_id
                    == athlete_profile_id,
                    TrainingSessionModel.activity_id.is_not(
                        None
                    ),
                )
            )

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
                    ActivityModel.id.not_in(
                        linked_activity_ids
                    ),
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

            raise TrainingSessionRepositoryError(
                (
                    "Impossible de rechercher les "
                    "activités disponibles du jour."
                )
            ) from exc

    def _get_required_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> TrainingSessionModel:
        database_session = self.session.scalar(
            select(TrainingSessionModel).where(
                TrainingSessionModel.id == session_id,
                TrainingSessionModel.athlete_profile_id
                == athlete_profile_id,
            )
        )

        if database_session is None:
            raise TrainingSessionRepositoryError(
                "Séance introuvable."
            )

        return database_session

    @staticmethod
    def _to_domain(
        session: TrainingSessionModel,
    ) -> TrainingSession:
        return TrainingSession(
            id=session.id,
            date=session.date,
            type=session.type,
            sport_type=session.sport_type,
            title=session.title,
            description=session.description,
            duration_minutes=session.duration_minutes,
            planning_key=session.planning_key,
            planning_importance=(
                session.planning_importance
            ),
            distance_km=session.distance_km,
            elevation_gain_m=session.elevation_gain_m,
            intensity=session.intensity,
            heart_rate_zone=session.heart_rate_zone,
            prescription=session.prescription,
            status=session.status,
            activity_id=session.activity_id,
            intervals_external_id=session.intervals_external_id,
            intervals_event_id=session.intervals_event_id,
            intervals_sync_status=session.intervals_sync_status,
            intervals_last_synced_at=session.intervals_last_synced_at,
            intervals_payload_hash=session.intervals_payload_hash,
            intervals_sync_error=session.intervals_sync_error,
            coros_workout_id=session.coros_workout_id,
            coros_scheduled_date=session.coros_scheduled_date,
            coros_sync_status=session.coros_sync_status,
            coros_sync_started_at=session.coros_sync_started_at,
            coros_last_synced_at=session.coros_last_synced_at,
            coros_payload_hash=session.coros_payload_hash,
            coros_sync_error=session.coros_sync_error,
        )

    @staticmethod
    def _activity_to_domain(
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
            athlete_max_heart_rate=(
                activity.athlete_max_heart_rate
            ),
            average_cadence=activity.average_cadence,
            average_stride_m=activity.average_stride_m,
            average_stance_time_ms=(
                activity.average_stance_time_ms
            ),
            average_vertical_oscillation_mm=(
                activity.average_vertical_oscillation_mm
            ),
            average_power_w=activity.average_power_w,
            average_altitude_m=activity.average_altitude_m,
            min_altitude_m=activity.min_altitude_m,
            max_altitude_m=activity.max_altitude_m,
            average_temperature_c=(
                activity.average_temperature_c
            ),
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
def test_sql_training_session_repository_lists_only_unlinked_activities() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlTrainingSessionRepository(db)

        linked_activity = create_activity(
            db,
            profile,
            provider_activity_id="i-linked",
            hour=7,
            name="Course déjà liée",
            feel=2,
        )

        available_activity = create_activity(
            db,
            profile,
            provider_activity_id="i-available",
            hour=8,
            name="Renforcement disponible",
            feel=1,
        )

        session = repository.save_session(
            profile.id,
            create_training_session(),
        )

        repository.link_activity(
            profile.id,
            session.id,
            linked_activity.id,
        )

        activities = (
            repository.list_unlinked_activities_for_date(
                profile.id,
                date(2026, 8, 9),
            )
        )

        assert len(activities) == 1

        assert (
            activities[0].id
            == available_activity.id
        )

        assert (
            activities[0].provider_activity_id
            == "i-available"
        )

    finally:
        db.close()
