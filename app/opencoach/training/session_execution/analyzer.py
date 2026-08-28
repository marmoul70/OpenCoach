"""Orchestration du comparateur prévu / réalisé."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import fields

from opencoach.models import (
    Activity,
    ActivityDetail,
    TrainingSession,
)

from .intensity import assess_session_intensity
from .load import assess_session_load
from .metric import NumericMetricAssessment
from .models import (
    SessionExecutionAssessment,
    SessionExecutionIntensityAssessment,
    SessionExecutionLoadAssessment,
    SessionExecutionStructureAssessment,
    SessionExecutionVolumeAssessment,
)
from .status import AssessmentStatus
from .thresholds import (
    DEFAULT_VOLUME_THRESHOLDS,
    VolumeAssessmentThresholds,
)
from .volume import assess_session_volume


def analyze_session_execution(
    session: TrainingSession,
    activity: Activity | None,
    activity_detail: ActivityDetail | None = None,
    *,
    volume_thresholds: VolumeAssessmentThresholds = (
        DEFAULT_VOLUME_THRESHOLDS
    ),
) -> SessionExecutionAssessment:
    """Évalue l'exécution complète d'une séance.

    Le matching activité / séance doit avoir été résolu avant
    cet appel. Ce moteur ne recherche jamais lui-même l'activité
    correspondant à une séance.
    """

    if session.id is None:
        raise ValueError(
            "Une séance persistée avec un identifiant "
            "est requise pour l'analyse d'exécution."
        )

    volume = assess_session_volume(
        session,
        activity,
        thresholds=volume_thresholds,
    )

    intensity = assess_session_intensity(
        session,
        activity,
        activity_detail,
    )

    load = assess_session_load(
        session,
        activity,
    )

    structure = (
        SessionExecutionStructureAssessment()
    )

    overall_status = _resolve_overall_status(
        session=session,
        activity=activity,
        volume=volume,
        intensity=intensity,
        load=load,
        structure=structure,
    )

    observations = _build_observations(
        session=session,
        activity=activity,
        overall_status=overall_status,
    )

    return SessionExecutionAssessment(
        session_id=session.id,
        activity_id=(
            activity.id
            if activity is not None
            else None
        ),
        overall_status=overall_status,
        volume=volume,
        intensity=intensity,
        load=load,
        structure=structure,
        observations=observations,
    )


def _resolve_overall_status(
    *,
    session: TrainingSession,
    activity: Activity | None,
    volume: SessionExecutionVolumeAssessment,
    intensity: SessionExecutionIntensityAssessment,
    load: SessionExecutionLoadAssessment,
    structure: SessionExecutionStructureAssessment,
) -> AssessmentStatus:
    """Calcule le statut global sans score opaque."""

    if session.type == "rest":
        if activity is None:
            return AssessmentStatus.COMPLIANT

    elif activity is None:
        return AssessmentStatus.NON_COMPLIANT

    statuses = tuple(
        _iter_metric_statuses(
            volume=volume,
            intensity=intensity,
            load=load,
            structure=structure,
        )
    )

    if AssessmentStatus.NON_COMPLIANT in statuses:
        return AssessmentStatus.NON_COMPLIANT

    if AssessmentStatus.PARTIAL in statuses:
        return AssessmentStatus.PARTIAL

    if AssessmentStatus.COMPLIANT in statuses:
        return AssessmentStatus.COMPLIANT

    if (
        AssessmentStatus.INSUFFICIENT_DATA
        in statuses
    ):
        return AssessmentStatus.INSUFFICIENT_DATA

    return AssessmentStatus.NOT_APPLICABLE


def _iter_metric_statuses(
    *,
    volume: SessionExecutionVolumeAssessment,
    intensity: SessionExecutionIntensityAssessment,
    load: SessionExecutionLoadAssessment,
    structure: SessionExecutionStructureAssessment,
) -> Iterable[AssessmentStatus]:
    """Retourne les statuts des métriques réellement présentes."""

    sections = (
        volume,
        intensity,
        load,
        structure,
    )

    for section in sections:
        for field in fields(section):
            metric = getattr(
                section,
                field.name,
            )

            if isinstance(
                metric,
                NumericMetricAssessment,
            ):
                yield metric.status


def _build_observations(
    *,
    session: TrainingSession,
    activity: Activity | None,
    overall_status: AssessmentStatus,
) -> tuple[str, ...]:
    """Construit quelques observations déterministes globales."""

    observations: list[str] = []

    if session.type == "rest":
        if activity is None:
            observations.append(
                "Le repos prescrit a été respecté."
            )
        else:
            observations.append(
                "Une activité est associée à une "
                "séance de repos."
            )

    elif activity is None:
        observations.append(
            "Aucune activité n'est associée "
            "à la séance prévue."
        )

    if (
        overall_status
        is AssessmentStatus.COMPLIANT
        and session.type != "rest"
    ):
        observations.append(
            "Les indicateurs disponibles sont "
            "globalement conformes à la prescription."
        )

    elif (
        overall_status
        is AssessmentStatus.PARTIAL
    ):
        observations.append(
            "La séance présente un ou plusieurs "
            "écarts modérés par rapport à la prescription."
        )

    elif (
        overall_status
        is AssessmentStatus.NON_COMPLIANT
        and activity is not None
    ):
        observations.append(
            "Au moins un indicateur présente un écart "
            "important par rapport à la prescription."
        )

    elif (
        overall_status
        is AssessmentStatus.INSUFFICIENT_DATA
    ):
        observations.append(
            "Les données disponibles sont insuffisantes "
            "pour conclure sur l'exécution de la séance."
        )

    return tuple(
        observations
    )
