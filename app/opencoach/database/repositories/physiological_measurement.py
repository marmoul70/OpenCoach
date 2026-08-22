from abc import ABC, abstractmethod
from uuid import UUID

from opencoach.models import (
    PhysiologicalMeasurement,
    PhysiologicalMetric,
)


class PhysiologicalMeasurementRepository(ABC):
    """Abstraction de persistance des mesures physiologiques."""

    @abstractmethod
    def save_measurement(
        self,
        athlete_profile_id: UUID,
        measurement: PhysiologicalMeasurement,
    ) -> PhysiologicalMeasurement:
        """Crée ou met à jour une mesure physiologique."""
        raise NotImplementedError

    @abstractmethod
    def get_measurement(
        self,
        athlete_profile_id: UUID,
        measurement_id: UUID,
    ) -> PhysiologicalMeasurement | None:
        """Retourne une mesure par identifiant."""
        raise NotImplementedError

    @abstractmethod
    def list_measurements(
        self,
        athlete_profile_id: UUID,
    ) -> list[PhysiologicalMeasurement]:
        """Retourne toutes les mesures de l'athlète."""
        raise NotImplementedError

    @abstractmethod
    def list_measurements_by_metric(
        self,
        athlete_profile_id: UUID,
        metric: PhysiologicalMetric,
    ) -> list[PhysiologicalMeasurement]:
        """Retourne l'historique d'une métrique."""
        raise NotImplementedError

    @abstractmethod
    def get_latest_measurement(
        self,
        athlete_profile_id: UUID,
        metric: PhysiologicalMetric,
    ) -> PhysiologicalMeasurement | None:
        """Retourne la mesure la plus récente d'une métrique."""
        raise NotImplementedError

    @abstractmethod
    def delete_measurement(
        self,
        athlete_profile_id: UUID,
        measurement_id: UUID,
    ) -> None:
        """Supprime une mesure physiologique."""
        raise NotImplementedError
