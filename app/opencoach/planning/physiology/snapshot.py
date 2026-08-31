from dataclasses import dataclass, field
from typing import Literal

from opencoach.models import (
    HeartRateZones,
    PhysiologicalMeasurement,
    PhysiologicalMetric,
)

from opencoach.planning.physiology.freshness import (
    PhysiologicalFreshnessAssessment,
)


CalibrationMetricSource = Literal[
    "history",
    "legacy_profile",
    "missing",
]


@dataclass(frozen=True)
class PhysiologicalCalibrationMetric:
    """État consolidé d'une métrique physiologique."""

    metric: PhysiologicalMetric

    value: float | None
    source: CalibrationMetricSource

    measurement: PhysiologicalMeasurement | None
    freshness: PhysiologicalFreshnessAssessment | None

    usable: bool
    recalibration_recommended: bool

    reason: str


@dataclass(frozen=True)
class PhysiologicalCalibrationSnapshot:
    """Vue complète de la calibration physiologique d'un athlète."""

    vma: PhysiologicalCalibrationMetric
    max_heart_rate: PhysiologicalCalibrationMetric
    resting_heart_rate: PhysiologicalCalibrationMetric
    threshold_heart_rate_1: PhysiologicalCalibrationMetric
    threshold_heart_rate_2: PhysiologicalCalibrationMetric

    heart_rate_zones: HeartRateZones = field(
        default_factory=HeartRateZones,
    )

    @property
    def metrics(
        self,
    ) -> tuple[PhysiologicalCalibrationMetric, ...]:
        """Retourne toutes les métriques dans un ordre stable."""

        return (
            self.vma,
            self.max_heart_rate,
            self.resting_heart_rate,
            self.threshold_heart_rate_1,
            self.threshold_heart_rate_2,
        )

    @property
    def missing_metrics(
        self,
    ) -> tuple[PhysiologicalCalibrationMetric, ...]:
        """Retourne les métriques totalement absentes."""

        return tuple(
            metric
            for metric in self.metrics
            if metric.source == "missing"
        )

    @property
    def recalibration_metrics(
        self,
    ) -> tuple[PhysiologicalCalibrationMetric, ...]:
        """Retourne les métriques nécessitant une recalibration."""

        return tuple(
            metric
            for metric in self.metrics
            if metric.recalibration_recommended
        )

    @property
    def usable_metrics(
        self,
    ) -> tuple[PhysiologicalCalibrationMetric, ...]:
        """Retourne les métriques actuellement utilisables."""

        return tuple(
            metric
            for metric in self.metrics
            if metric.usable
        )

    @property
    def has_calibration_needs(self) -> bool:
        """Indique si une calibration ou recalibration est nécessaire."""

        return bool(
            self.missing_metrics
            or self.recalibration_metrics
        )
