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

@dataclass(frozen=True, slots=True)
class TargetAdherenceThresholds:
    """Seuils de temps passé dans une cible prescrite."""

    compliant_percent: float = 80.0
    partial_percent: float = 60.0

    def __post_init__(self) -> None:
        if not (
            0.0
            <= self.partial_percent
            <= self.compliant_percent
            <= 100.0
        ):
            raise ValueError(
                "Les seuils d'adhérence doivent respecter "
                "0 <= partial <= compliant <= 100."
            )


DEFAULT_TARGET_ADHERENCE_THRESHOLDS = (
    TargetAdherenceThresholds()
)

@dataclass(frozen=True, slots=True)
class StructureAssessmentThresholds:
    """Seuils déterministes d'évaluation du fractionné."""

    repetition_partial_percent: float = 80.0

    work_distance_compliant_percent: float = 10.0
    work_distance_partial_percent: float = 20.0

    work_duration_partial_percent: float = 10.0

    recovery_compliant_percent: float = 15.0
    recovery_partial_percent: float = 30.0

    regularity_compliant_percent: float = 5.0
    regularity_partial_percent: float = 10.0

    degradation_compliant_percent: float = 5.0
    degradation_partial_percent: float = 10.0

    def __post_init__(self) -> None:
        if not (
            0.0
            <= self.repetition_partial_percent
            <= 100.0
        ):
            raise ValueError(
                "Le seuil partiel de répétitions "
                "doit être compris entre 0 et 100."
            )

        pairs = (
            (
                self.work_distance_compliant_percent,
                self.work_distance_partial_percent,
            ),
            (
                self.recovery_compliant_percent,
                self.recovery_partial_percent,
            ),
            (
                self.regularity_compliant_percent,
                self.regularity_partial_percent,
            ),
            (
                self.degradation_compliant_percent,
                self.degradation_partial_percent,
            ),
        )

        for compliant, partial in pairs:
            if compliant < 0 or partial < compliant:
                raise ValueError(
                    "Les seuils structurels sont invalides."
                )

        if self.work_duration_partial_percent < 0:
            raise ValueError(
                "La tolérance de durée ne peut pas être négative."
            )


DEFAULT_STRUCTURE_THRESHOLDS = (
    StructureAssessmentThresholds()
)
