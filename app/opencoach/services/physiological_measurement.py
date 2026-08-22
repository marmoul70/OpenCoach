from uuid import UUID

from opencoach.database.repositories import (
    PhysiologicalMeasurementRepository,
)
from opencoach.models import (
    PhysiologicalMeasurement,
)

from .profile import ProfileService


class PhysiologicalMeasurementService:
    """Gère l'historique et la valeur physiologique courante."""

    def __init__(
        self,
        *,
        measurement_repository: PhysiologicalMeasurementRepository,
        profile_service: ProfileService,
    ) -> None:
        self.measurement_repository = (
            measurement_repository
        )
        self.profile_service = profile_service

    def record_measurement(
        self,
        *,
        athlete_profile_id: UUID,
        measurement: PhysiologicalMeasurement,
    ) -> PhysiologicalMeasurement:
        """Enregistre une mesure et synchronise le profil si nécessaire."""

        saved = (
            self.measurement_repository.save_measurement(
                athlete_profile_id,
                measurement,
            )
        )

        latest = (
            self.measurement_repository.get_latest_measurement(
                athlete_profile_id,
                measurement.metric,
            )
        )

        if (
            latest is not None
            and latest.id == saved.id
        ):
            self._update_current_profile_value(
                metric=saved.metric,
                value=saved.value,
            )

        return saved

    def _update_current_profile_value(
        self,
        *,
        metric: str,
        value: float,
    ) -> None:
        athlete = self.profile_service.get_profile()

        physiology = athlete.physiology

        if metric == "vma":
            physiology.vma = value

        elif metric == "max_heart_rate":
            physiology.max_heart_rate = round(
                value
            )

        elif metric == "resting_heart_rate":
            physiology.resting_heart_rate = round(
                value
            )

        elif metric == "threshold_heart_rate_1":
            physiology.threshold_heart_rate_1 = round(
                value
            )

        elif metric == "threshold_heart_rate_2":
            physiology.threshold_heart_rate_2 = round(
                value
            )

        else:
            raise ValueError(
                f"Métrique physiologique non supportée : {metric}"
            )

        self.profile_service.update_profile(
            athlete
        )
