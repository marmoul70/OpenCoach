from .repetition_measurement import (
    MeasuredRepetition,
    measure_refined_repetition,
)
from .repetition_boundary import (
    RefinedRepetitionBoundary,
    refine_repetition_boundary,
)
from .repetition_transition import (
    RepetitionTransitionEvidence,
    score_repetition_transition,
)
from .repetition_selection import (
    EvidencedRepetitionCandidate,
    select_evidenced_distance_repetitions,
)
from .repetition_evidence import (
    RepetitionEvidence,
    RepetitionEvidenceScorer,
    score_repetition_candidate,
)
from .stream_repetition_detection import (
    build_distance_repetition_candidates,
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
    "MeasuredRepetition",
    "measure_refined_repetition",
    "RepetitionDetectionResult",
    "RepetitionEvidence",
    "RefinedRepetitionBoundary",
    "refine_repetition_boundary",
    "RepetitionTransitionEvidence",
    "score_repetition_transition",
    "RepetitionEvidenceScorer",
    "EvidencedRepetitionCandidate",
    "select_evidenced_distance_repetitions",
    "score_repetition_candidate",
    "detect_repetitions",
    "RepetitionTarget",
    "StructuredSessionPrescription",
    "parse_structured_session_prescription",
    "DEFAULT_TARGET_ADHERENCE_THRESHOLDS",
    "StreamRangeAnalysis",
    "StreamRepetitionCandidate",
    "detect_distance_repetitions_from_streams",
    "build_distance_repetition_candidates",
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
