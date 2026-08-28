"""Évaluation déterministe de l'exécution des séances OpenCoach."""

from .metric import (
    NumericMetricAssessment,
    NumericTarget,
)
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
    MetricTolerance,
    VolumeAssessmentThresholds,
)
from .volume import assess_session_volume

__all__ = [
    "AssessmentStatus",
    "DEFAULT_VOLUME_THRESHOLDS",
    "MetricTolerance",
    "NumericMetricAssessment",
    "NumericTarget",
    "SessionExecutionAssessment",
    "SessionExecutionIntensityAssessment",
    "SessionExecutionLoadAssessment",
    "SessionExecutionStructureAssessment",
    "SessionExecutionVolumeAssessment",
    "VolumeAssessmentThresholds",
    "assess_session_volume",
]
