"""Modèles structurés d'évaluation d'une séance réalisée."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
from typing import TYPE_CHECKING

from .metric import NumericMetricAssessment
from .status import AssessmentStatus


if TYPE_CHECKING:
    from .goal_analysis.models import (
        SessionGoalAnalysis,
    )


@dataclass(frozen=True, slots=True)
class SessionExecutionVolumeAssessment:
    """Évaluation du volume réellement effectué."""

    duration: NumericMetricAssessment | None = None
    distance: NumericMetricAssessment | None = None
    elevation_gain: NumericMetricAssessment | None = None


@dataclass(frozen=True, slots=True)
class SessionExecutionIntensityAssessment:
    """Évaluation de l'intensité réellement produite."""

    average_heart_rate: NumericMetricAssessment | None = None

    average_speed: NumericMetricAssessment | None = None
    average_pace: NumericMetricAssessment | None = None

    average_vma_percent: NumericMetricAssessment | None = None

    time_in_heart_rate_target: (
        NumericMetricAssessment | None
    ) = None

    time_in_pace_target: (
        NumericMetricAssessment | None
    ) = None


@dataclass(frozen=True, slots=True)
class SessionExecutionLoadAssessment:
    """Évaluation de la charge d'entraînement."""

    training_load: NumericMetricAssessment | None = None


@dataclass(frozen=True, slots=True)
class SessionExecutionStructureAssessment:
    """Évaluation structurelle des séances fractionnées."""

    repetition_count: NumericMetricAssessment | None = None

    work_duration: NumericMetricAssessment | None = None
    work_distance: NumericMetricAssessment | None = None

    recovery_duration: NumericMetricAssessment | None = None

    repetition_regularity: (
        NumericMetricAssessment | None
    ) = None

    repetition_degradation: (
        NumericMetricAssessment | None
    ) = None


@dataclass(frozen=True, slots=True)
class SessionExecutionAssessment:
    """Évaluation complète d'une séance prévue/réalisée.

    L'association séance/activité est supposée déjà résolue.
    Ce modèle n'effectue aucun matching d'activité.
    """

    session_id: UUID
    activity_id: UUID | None

    overall_status: AssessmentStatus

    volume: SessionExecutionVolumeAssessment
    intensity: SessionExecutionIntensityAssessment
    load: SessionExecutionLoadAssessment
    structure: SessionExecutionStructureAssessment

    observations: tuple[str, ...] = ()

    # Statut technique brut calculé à partir de toutes les
    # métriques disponibles, indépendamment de leur importance
    # pour l'objectif physiologique de la séance.
    technical_status: AssessmentStatus | None = None

    # Interprétation métier orientée objectif.
    goal_analysis: "SessionGoalAnalysis | None" = None
