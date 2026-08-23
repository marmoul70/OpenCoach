from dataclasses import dataclass
from typing import Literal

from opencoach.models import AthleteProfile


CalibrationStatus = Literal[
    "missing",
    "available",
]


@dataclass(frozen=True)
class PhysiologicalMetricAssessment:
    """État d'une métrique physiologique utilisée par le coach."""

    metric: str
    value: int | float | None

    status: CalibrationStatus

    calibration_recommended: bool
    reason: str


@dataclass(frozen=True)
class PhysiologicalCalibrationAssessment:
    """Évalue la calibration physiologique disponible pour l'athlète."""

    max_heart_rate: PhysiologicalMetricAssessment
    resting_heart_rate: PhysiologicalMetricAssessment
    vma: PhysiologicalMetricAssessment
    threshold_heart_rate_1: PhysiologicalMetricAssessment
    threshold_heart_rate_2: PhysiologicalMetricAssessment

    basic_intensity_prescription_ready: bool
    threshold_prescription_ready: bool

    recommended_assessments: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def has_missing_metrics(self) -> bool:
        """Indique si au moins une métrique physiologique manque."""

        return any(
            metric.status == "missing"
            for metric in (
                self.max_heart_rate,
                self.resting_heart_rate,
                self.vma,
                self.threshold_heart_rate_1,
                self.threshold_heart_rate_2,
            )
        )


def assess_physiological_calibration(
    athlete: AthleteProfile,
) -> PhysiologicalCalibrationAssessment:
    """Évalue les références physiologiques disponibles."""

    physiology = athlete.physiology

    max_heart_rate = _assess_metric(
        metric="max_heart_rate",
        value=physiology.max_heart_rate,
        calibration_recommended=True,
        missing_reason=(
            "La FC maximale n'est pas renseignée."
        ),
    )

    resting_heart_rate = _assess_metric(
        metric="resting_heart_rate",
        value=physiology.resting_heart_rate,
        calibration_recommended=False,
        missing_reason=(
            "La FC de repos n'est pas renseignée."
        ),
    )

    vma = _assess_metric(
        metric="vma",
        value=physiology.vma,
        calibration_recommended=True,
        missing_reason=(
            "La VMA n'est pas renseignée."
        ),
    )

    threshold_heart_rate_1 = _assess_metric(
        metric="threshold_heart_rate_1",
        value=physiology.threshold_heart_rate_1,
        calibration_recommended=True,
        missing_reason=(
            "Le seuil SV1 n'est pas renseigné."
        ),
    )

    threshold_heart_rate_2 = _assess_metric(
        metric="threshold_heart_rate_2",
        value=physiology.threshold_heart_rate_2,
        calibration_recommended=True,
        missing_reason=(
            "Le seuil SV2 n'est pas renseigné."
        ),
    )

    basic_intensity_prescription_ready = any(
        value is not None
        for value in (
            physiology.max_heart_rate,
            physiology.vma,
            physiology.threshold_heart_rate_2,
        )
    )

    threshold_prescription_ready = (
        physiology.threshold_heart_rate_1
        is not None
        and physiology.threshold_heart_rate_2
        is not None
    )

    recommended_assessments: list[str] = []

    if physiology.vma is None:
        recommended_assessments.append(
            "vma_calibration"
        )

    if physiology.max_heart_rate is None:
        recommended_assessments.append(
            "max_heart_rate_calibration"
        )

    if (
        physiology.threshold_heart_rate_1 is None
        or physiology.threshold_heart_rate_2 is None
    ):
        recommended_assessments.append(
            "threshold_calibration"
        )

    reasons: list[str] = []

    if basic_intensity_prescription_ready:
        reasons.append(
            "Au moins une référence permet une prescription "
            "élémentaire des intensités."
        )
    else:
        reasons.append(
            "Aucune référence suffisante n'est disponible "
            "pour prescrire précisément les intensités."
        )

    if threshold_prescription_ready:
        reasons.append(
            "Les seuils SV1 et SV2 sont disponibles."
        )
    else:
        reasons.append(
            "La calibration des seuils est incomplète."
        )

    if recommended_assessments:
        reasons.append(
            "Une ou plusieurs séances de calibration pourront "
            "être intégrées au planning."
        )

    return PhysiologicalCalibrationAssessment(
        max_heart_rate=max_heart_rate,
        resting_heart_rate=resting_heart_rate,
        vma=vma,
        threshold_heart_rate_1=(
            threshold_heart_rate_1
        ),
        threshold_heart_rate_2=(
            threshold_heart_rate_2
        ),
        basic_intensity_prescription_ready=(
            basic_intensity_prescription_ready
        ),
        threshold_prescription_ready=(
            threshold_prescription_ready
        ),
        recommended_assessments=tuple(
            recommended_assessments
        ),
        reasons=tuple(reasons),
    )


def _assess_metric(
    *,
    metric: str,
    value: int | float | None,
    calibration_recommended: bool,
    missing_reason: str,
) -> PhysiologicalMetricAssessment:
    if value is None:
        return PhysiologicalMetricAssessment(
            metric=metric,
            value=None,
            status="missing",
            calibration_recommended=(
                calibration_recommended
            ),
            reason=missing_reason,
        )

    return PhysiologicalMetricAssessment(
        metric=metric,
        value=value,
        status="available",
        calibration_recommended=False,
        reason="Métrique physiologique disponible.",
    )
