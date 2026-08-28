from .stream_repetition_detection import (
    StreamRepetitionCandidate,
    detect_distance_repetitions_from_streams,
)
from .structure import assess_session_structure
from .stream_analysis import (
    StreamRangeAnalysis,
    calculate_time_in_range,
)
"""Évaluation déterministe de l'exécution des séances OpenCoach."""

from .analyzer import analyze_session_execution
from .intensity import assess_session_intensity
from .interval_detection import (
    ObservedRepetition,
    RepetitionDetectionResult,
    detect_repetitions,
)
from .interval_prescription import (
    IntervalSetPrescription,
    RepetitionTarget,
    StructuredSessionPrescription,
    parse_structured_session_prescription,
)
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
    DEFAULT_TARGET_ADHERENCE_THRESHOLDS,
    TargetAdherenceThresholds,
    DEFAULT_VOLUME_THRESHOLDS,
    MetricTolerance,
    VolumeAssessmentThresholds,
)
from .volume import assess_session_volume

__all__ = [
    "AssessmentStatus",
    "IntervalSetPrescription",
    "ObservedRepetition",
    "RepetitionDetectionResult",
    "detect_repetitions",
    "RepetitionTarget",
    "StructuredSessionPrescription",
    "parse_structured_session_prescription",
    "DEFAULT_TARGET_ADHERENCE_THRESHOLDS",
    "StreamRangeAnalysis",
    "StreamRepetitionCandidate",
    "detect_distance_repetitions_from_streams",
    "TargetAdherenceThresholds",
    "calculate_time_in_range",
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
    "assess_session_structure",
    "assess_session_load",
    "assess_session_volume",
]
