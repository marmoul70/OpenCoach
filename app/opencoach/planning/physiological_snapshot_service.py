from datetime import date
from uuid import UUID

from opencoach.database.repositories import (
    PhysiologicalMeasurementRepository,
)
from opencoach.models import (
    AthleteProfile,
    PhysiologicalMetric,
)

from .physiological_freshness import (
    assess_measurement_freshness,
)
from .physiological_snapshot import (
    PhysiologicalCalibrationMetric,
    PhysiologicalCalibrationSnapshot,
)


class PhysiologicalCalibrationSnapshotService:
    """Construit la vue consolidée de calibration physiologique."""

    def __init__(
        self,
        measurement_repository: PhysiologicalMeasurementRepository,
    ) -> None:
        self.measurement_repository = (
            measurement_repository
        )

    def build(
        self,
        *,
        athlete_profile_id: UUID,
        athlete: AthleteProfile,
        reference_date: date,
    ) -> PhysiologicalCalibrationSnapshot:
        """Construit l'état physiologique courant de l'athlète."""

        return PhysiologicalCalibrationSnapshot(
            vma=self._build_metric(
                athlete_profile_id=athlete_profile_id,
                metric="vma",
                profile_value=athlete.physiology.vma,
                reference_date=reference_date,
            ),
            max_heart_rate=self._build_metric(
                athlete_profile_id=athlete_profile_id,
                metric="max_heart_rate",
                profile_value=(
                    athlete.physiology.max_heart_rate
                ),
                reference_date=reference_date,
            ),
            resting_heart_rate=self._build_metric(
                athlete_profile_id=athlete_profile_id,
                metric="resting_heart_rate",
                profile_value=(
                    athlete.physiology.resting_heart_rate
                ),
                reference_date=reference_date,
            ),
            threshold_heart_rate_1=self._build_metric(
                athlete_profile_id=athlete_profile_id,
                metric="threshold_heart_rate_1",
                profile_value=(
                    athlete.physiology.threshold_heart_rate_1
                ),
                reference_date=reference_date,
            ),
            threshold_heart_rate_2=self._build_metric(
                athlete_profile_id=athlete_profile_id,
                metric="threshold_heart_rate_2",
                profile_value=(
                    athlete.physiology.threshold_heart_rate_2
                ),
                reference_date=reference_date,
            ),
        )

    def _build_metric(
        self,
        *,
        athlete_profile_id: UUID,
        metric: PhysiologicalMetric,
        profile_value: int | float | None,
        reference_date: date,
    ) -> PhysiologicalCalibrationMetric:
        latest = (
            self.measurement_repository.get_latest_measurement(
                athlete_profile_id,
                metric,
            )
        )

        if latest is not None:
            freshness = assess_measurement_freshness(
                measurement=latest,
                reference_date=reference_date,
            )

            return PhysiologicalCalibrationMetric(
                metric=metric,
                value=latest.value,
                source="history",
                measurement=latest,
                freshness=freshness,
                usable=freshness.usable,
                recalibration_recommended=(
                    freshness.recalibration_recommended
                ),
                reason=freshness.reason,
            )

        if profile_value is not None:
            return PhysiologicalCalibrationMetric(
                metric=metric,
                value=float(profile_value),
                source="legacy_profile",
                measurement=None,
                freshness=None,
                usable=True,
                recalibration_recommended=True,
                reason=(
                    "La valeur existe dans le profil mais son origine "
                    "et sa date de mesure sont inconnues."
                ),
            )

        return PhysiologicalCalibrationMetric(
            metric=metric,
            value=None,
            source="missing",
            measurement=None,
            freshness=None,
            usable=False,
            recalibration_recommended=True,
            reason=(
                "Aucune valeur physiologique n'est disponible."
            ),
        )
