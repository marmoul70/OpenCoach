"""Analyse déterministe du volume prévu et réalisé."""

from __future__ import annotations

from opencoach.models import Activity, TrainingSession

from .metric import (
    NumericMetricAssessment,
    NumericTarget,
)
from .models import SessionExecutionVolumeAssessment
from .status import AssessmentStatus
from .thresholds import (
    DEFAULT_VOLUME_THRESHOLDS,
    MetricTolerance,
    VolumeAssessmentThresholds,
)


def assess_session_volume(
    session: TrainingSession,
    activity: Activity | None,
    *,
    thresholds: VolumeAssessmentThresholds = (
        DEFAULT_VOLUME_THRESHOLDS
    ),
) -> SessionExecutionVolumeAssessment:
    """Compare les principaux volumes prescrits et réalisés.

    Le matching entre activité et séance n'est pas effectué ici.
    L'activité fournie est supposée avoir déjà été associée
    à la séance.
    """

    return SessionExecutionVolumeAssessment(
        duration=_assess_duration(
            session,
            activity,
            thresholds.duration,
        ),
        distance=_assess_distance(
            session,
            activity,
            thresholds.distance,
        ),
        elevation_gain=_assess_elevation_gain(
            session,
            activity,
            thresholds.elevation_gain,
        ),
    )


def _assess_duration(
    session: TrainingSession,
    activity: Activity | None,
    tolerance: MetricTolerance,
) -> NumericMetricAssessment:
    planned = float(session.duration_minutes)

    target = NumericTarget.exact(
        planned,
        "min",
    )

    if activity is None:
        return _insufficient_metric(
            key="duration",
            label="Durée",
            target=target,
            details="Aucune activité associée à la séance.",
        )

    seconds = (
        activity.moving_time_seconds
        if activity.moving_time_seconds is not None
        else activity.elapsed_time_seconds
    )

    if seconds is None:
        return _insufficient_metric(
            key="duration",
            label="Durée",
            target=target,
            details=(
                "La durée de l'activité n'est pas disponible."
            ),
        )

    actual = seconds / 60.0

    return _compare_exact_value(
        key="duration",
        label="Durée",
        target=planned,
        actual=actual,
        unit="min",
        tolerance=tolerance,
    )


def _assess_distance(
    session: TrainingSession,
    activity: Activity | None,
    tolerance: MetricTolerance,
) -> NumericMetricAssessment:
    planned = session.distance_km

    if planned is None or planned <= 0:
        return _not_applicable_metric(
            key="distance",
            label="Distance",
            details=(
                "Aucune distance n'est prescrite "
                "pour cette séance."
            ),
        )

    target = NumericTarget.exact(
        planned,
        "km",
    )

    if activity is None:
        return _insufficient_metric(
            key="distance",
            label="Distance",
            target=target,
            details="Aucune activité associée à la séance.",
        )

    if activity.distance_m is None:
        return _insufficient_metric(
            key="distance",
            label="Distance",
            target=target,
            details=(
                "La distance de l'activité "
                "n'est pas disponible."
            ),
        )

    actual = activity.distance_m / 1000.0

    return _compare_exact_value(
        key="distance",
        label="Distance",
        target=planned,
        actual=actual,
        unit="km",
        tolerance=tolerance,
    )


def _assess_elevation_gain(
    session: TrainingSession,
    activity: Activity | None,
    tolerance: MetricTolerance,
) -> NumericMetricAssessment:
    planned = session.elevation_gain_m

    if planned is None or planned <= 0:
        return _not_applicable_metric(
            key="elevation_gain",
            label="Dénivelé positif",
            details=(
                "Aucun dénivelé positif n'est prescrit "
                "pour cette séance."
            ),
        )

    target = NumericTarget.exact(
        planned,
        "m",
    )

    if activity is None:
        return _insufficient_metric(
            key="elevation_gain",
            label="Dénivelé positif",
            target=target,
            details="Aucune activité associée à la séance.",
        )

    if activity.elevation_gain_m is None:
        return _insufficient_metric(
            key="elevation_gain",
            label="Dénivelé positif",
            target=target,
            details=(
                "Le dénivelé positif de l'activité "
                "n'est pas disponible."
            ),
        )

    return _compare_exact_value(
        key="elevation_gain",
        label="Dénivelé positif",
        target=planned,
        actual=activity.elevation_gain_m,
        unit="m",
        tolerance=tolerance,
    )


def _compare_exact_value(
    *,
    key: str,
    label: str,
    target: float,
    actual: float,
    unit: str,
    tolerance: MetricTolerance,
) -> NumericMetricAssessment:
    """Compare une valeur réalisée à une prescription exacte."""

    delta = actual - target

    delta_percent = (
        delta / target * 100.0
    )

    absolute_delta_percent = abs(
        delta_percent
    )

    if (
        absolute_delta_percent
        <= tolerance.compliant_percent
    ):
        status = AssessmentStatus.COMPLIANT

    elif (
        absolute_delta_percent
        <= tolerance.partial_percent
    ):
        status = AssessmentStatus.PARTIAL

    else:
        status = AssessmentStatus.NON_COMPLIANT

    return NumericMetricAssessment(
        key=key,
        label=label,
        status=status,
        target=NumericTarget.exact(
            round(target, 2),
            unit,
        ),
        actual_value=round(
            actual,
            2,
        ),
        delta=round(
            delta,
            2,
        ),
        delta_percent=round(
            delta_percent,
            2,
        ),
    )


def _not_applicable_metric(
    *,
    key: str,
    label: str,
    details: str,
) -> NumericMetricAssessment:
    return NumericMetricAssessment(
        key=key,
        label=label,
        status=AssessmentStatus.NOT_APPLICABLE,
        details=details,
    )


def _insufficient_metric(
    *,
    key: str,
    label: str,
    target: NumericTarget,
    details: str,
) -> NumericMetricAssessment:
    return NumericMetricAssessment(
        key=key,
        label=label,
        status=AssessmentStatus.INSUFFICIENT_DATA,
        target=target,
        details=details,
    )
