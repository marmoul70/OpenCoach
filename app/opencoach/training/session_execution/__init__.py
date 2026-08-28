"""Évaluation déterministe de l'exécution des séances OpenCoach."""

from .analyzer import analyze_session_execution
from .intensity import assess_session_intensity
from .load import assess_session_load
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
    "analyze_session_execution",
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
    "assess_session_intensity",
    "assess_session_load",
    "assess_session_volume",
]
