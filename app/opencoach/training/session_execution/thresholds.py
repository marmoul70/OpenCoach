"""Tolérances métier du comparateur d'exécution de séance."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricTolerance:
    """Tolérances relatives d'un indicateur numérique.

    Les valeurs sont exprimées en pourcentage d'écart absolu
    par rapport à la prescription.
    """

    compliant_percent: float
    partial_percent: float

    def __post_init__(self) -> None:
        if self.compliant_percent < 0:
            raise ValueError(
                "La tolérance conforme ne peut pas être négative."
            )

        if self.partial_percent < self.compliant_percent:
            raise ValueError(
                "La tolérance partielle ne peut pas être "
                "inférieure à la tolérance conforme."
            )


@dataclass(frozen=True, slots=True)
class VolumeAssessmentThresholds:
    """Tolérances des indicateurs de volume."""

    duration: MetricTolerance = MetricTolerance(
        compliant_percent=10.0,
        partial_percent=20.0,
    )

    distance: MetricTolerance = MetricTolerance(
        compliant_percent=10.0,
        partial_percent=20.0,
    )

    elevation_gain: MetricTolerance = MetricTolerance(
        compliant_percent=15.0,
        partial_percent=30.0,
    )


DEFAULT_VOLUME_THRESHOLDS = VolumeAssessmentThresholds()
