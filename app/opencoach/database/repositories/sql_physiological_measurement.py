from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    PhysiologicalMeasurement as PhysiologicalMeasurementModel,
)
from opencoach.models import (
    PhysiologicalMeasurement,
    PhysiologicalMetric,
)

from .errors import (
    PhysiologicalMeasurementRepositoryError,
)
from .physiological_measurement import (
    PhysiologicalMeasurementRepository,
)


class SqlPhysiologicalMeasurementRepository(
    PhysiologicalMeasurementRepository,
):
    """Persiste l'historique des mesures physiologiques."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_measurement(
        self,
        athlete_profile_id: UUID,
        measurement: PhysiologicalMeasurement,
    ) -> PhysiologicalMeasurement:
        """Crée ou met à jour une mesure."""

        try:
            database_measurement = self.session.scalar(
                select(
                    PhysiologicalMeasurementModel
                ).where(
                    PhysiologicalMeasurementModel.id
                    == measurement.id,
                    PhysiologicalMeasurementModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_measurement is None:
                database_measurement = (
                    PhysiologicalMeasurementModel(
                        id=measurement.id,
                        athlete_profile_id=athlete_profile_id,
                    )
                )

                self.session.add(
                    database_measurement
                )

            database_measurement.metric = (
                measurement.metric
            )

            database_measurement.value = (
                measurement.value
            )

            database_measurement.measured_at = (
                measurement.measured_at
            )

            database_measurement.protocol = (
                measurement.protocol
            )

            database_measurement.source = (
                measurement.source
            )

            database_measurement.confidence = (
                measurement.confidence
            )

            database_measurement.notes = (
                measurement.notes
            )

            self.session.commit()
            self.session.refresh(
                database_measurement
            )

            return self._to_domain(
                database_measurement
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PhysiologicalMeasurementRepositoryError(
                "Impossible d'enregistrer la mesure physiologique."
            ) from exc

    def get_measurement(
        self,
        athlete_profile_id: UUID,
        measurement_id: UUID,
    ) -> PhysiologicalMeasurement | None:
        """Retourne une mesure par identifiant."""

        try:
            database_measurement = self.session.scalar(
                select(
                    PhysiologicalMeasurementModel
                ).where(
                    PhysiologicalMeasurementModel.id
                    == measurement_id,
                    PhysiologicalMeasurementModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_measurement is None:
                return None

            return self._to_domain(
                database_measurement
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PhysiologicalMeasurementRepositoryError(
                "Impossible de charger la mesure physiologique."
            ) from exc

    def list_measurements(
        self,
        athlete_profile_id: UUID,
    ) -> list[PhysiologicalMeasurement]:
        """Retourne toutes les mesures, de la plus récente à la plus ancienne."""

        try:
            statement = (
                select(
                    PhysiologicalMeasurementModel
                )
                .where(
                    PhysiologicalMeasurementModel.athlete_profile_id
                    == athlete_profile_id
                )
                .order_by(
                    PhysiologicalMeasurementModel.measured_at.desc(),
                    PhysiologicalMeasurementModel.created_at.desc(),
                )
            )

            measurements = self.session.scalars(
                statement
            ).all()

            return [
                self._to_domain(
                    measurement
                )
                for measurement in measurements
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PhysiologicalMeasurementRepositoryError(
                "Impossible de charger les mesures physiologiques."
            ) from exc

    def list_measurements_by_metric(
        self,
        athlete_profile_id: UUID,
        metric: PhysiologicalMetric,
    ) -> list[PhysiologicalMeasurement]:
        """Retourne l'historique d'une métrique."""

        try:
            statement = (
                select(
                    PhysiologicalMeasurementModel
                )
                .where(
                    PhysiologicalMeasurementModel.athlete_profile_id
                    == athlete_profile_id,
                    PhysiologicalMeasurementModel.metric
                    == metric,
                )
                .order_by(
                    PhysiologicalMeasurementModel.measured_at.desc(),
                    PhysiologicalMeasurementModel.created_at.desc(),
                )
            )

            measurements = self.session.scalars(
                statement
            ).all()

            return [
                self._to_domain(
                    measurement
                )
                for measurement in measurements
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PhysiologicalMeasurementRepositoryError(
                "Impossible de charger l'historique physiologique."
            ) from exc

    def get_latest_measurement(
        self,
        athlete_profile_id: UUID,
        metric: PhysiologicalMetric,
    ) -> PhysiologicalMeasurement | None:
        """Retourne la dernière mesure disponible d'une métrique."""

        try:
            statement = (
                select(
                    PhysiologicalMeasurementModel
                )
                .where(
                    PhysiologicalMeasurementModel.athlete_profile_id
                    == athlete_profile_id,
                    PhysiologicalMeasurementModel.metric
                    == metric,
                )
                .order_by(
                    PhysiologicalMeasurementModel.measured_at.desc(),
                    PhysiologicalMeasurementModel.created_at.desc(),
                )
                .limit(1)
            )

            measurement = self.session.scalar(
                statement
            )

            if measurement is None:
                return None

            return self._to_domain(
                measurement
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PhysiologicalMeasurementRepositoryError(
                "Impossible de charger la dernière mesure physiologique."
            ) from exc

    def delete_measurement(
        self,
        athlete_profile_id: UUID,
        measurement_id: UUID,
    ) -> None:
        """Supprime une mesure."""

        try:
            database_measurement = self.session.scalar(
                select(
                    PhysiologicalMeasurementModel
                ).where(
                    PhysiologicalMeasurementModel.id
                    == measurement_id,
                    PhysiologicalMeasurementModel.athlete_profile_id
                    == athlete_profile_id,
                )
            )

            if database_measurement is None:
                raise PhysiologicalMeasurementRepositoryError(
                    "Mesure physiologique introuvable."
                )

            self.session.delete(
                database_measurement
            )

            self.session.commit()

        except PhysiologicalMeasurementRepositoryError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PhysiologicalMeasurementRepositoryError(
                "Impossible de supprimer la mesure physiologique."
            ) from exc

    @staticmethod
    def _to_domain(
        measurement: PhysiologicalMeasurementModel,
    ) -> PhysiologicalMeasurement:
        """Convertit le modèle SQL en modèle métier."""

        return PhysiologicalMeasurement(
            id=measurement.id,
            metric=measurement.metric,
            value=measurement.value,
            measured_at=measurement.measured_at,
            protocol=measurement.protocol,
            source=measurement.source,
            confidence=measurement.confidence,
            notes=measurement.notes,
        )
