from opencoach.planning.athlete.availability import (
    DayAvailability,
    DayAvailabilityStatus,
    resolve_day_availability,
)
from .context import PlanningContext
from .quality import (
    PlanningContextAssessment,
    assess_planning_context,
)
from .service import PlanningContextService
from opencoach.planning.athlete.weekly_availability import (
    WeeklyAvailability,
    build_weekly_availability,
)
from opencoach.planning.athlete.candidates import (
    TrainingDayCandidate,
    rank_training_day_candidates,
)
from opencoach.planning.placement.session import (
    SessionPlacementContext,
    build_session_placement_context,
)
from opencoach.planning.placement.scoring import (
    SessionPlacementCandidate,
    rank_session_placement_candidates,
)
from opencoach.planning.placement.rules import (
    PlacementRuleResult,
    RuleSeverity,
    evaluate_placement_rules,
)
from opencoach.planning.placement.result import (
    SessionPlacementResult,
    build_session_placement_result,
)
from opencoach.planning.history.training import (
    TrainingHistorySnapshot,
)
from opencoach.planning.history.service import (
    TrainingHistorySnapshotService,
)
from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
    WeeklyTrainingAverages,
    calculate_training_history_metrics,
)
from opencoach.planning.athlete.capacity import (
    AthleteCapacityAssessment,
    CapacityConfidence,
    assess_athlete_capacity,
)
from opencoach.planning.athlete.capacity_profile_comparison import (
    CapacityMetricComparison,
    CapacityProfileComparison,
    ComparisonStatus,
    compare_capacity_to_profile,
)
from opencoach.planning.physiology.training_baseline import (
    AthleteTrainingBaseline,
    build_training_baseline,
)
from opencoach.planning.physiology.calibration import (
    CalibrationStatus,
    PhysiologicalCalibrationAssessment,
    PhysiologicalMetricAssessment,
    assess_physiological_calibration,
)
from opencoach.planning.physiology.freshness import (
    MeasurementFreshness,
    PhysiologicalFreshnessAssessment,
    PhysiologicalFreshnessPolicy,
    assess_measurement_freshness,
)
from opencoach.planning.physiology.snapshot import (
    CalibrationMetricSource,
    PhysiologicalCalibrationMetric,
    PhysiologicalCalibrationSnapshot,
)
from opencoach.planning.physiology.snapshot_service import (
    PhysiologicalCalibrationSnapshotService,
)
from opencoach.planning.assessment.need import (
    AssessmentNeed,
    AssessmentPriority,
    AssessmentType,
    identify_assessment_needs,
)
from opencoach.planning.assessment.protocol import (
    ASSESSMENT_PROTOCOLS,
    AssessmentProtocol,
    ProtocolEnvironment,
    ProtocolIntensity,
    get_assessment_protocol,
    get_assessment_protocols,
)
from opencoach.planning.assessment.protocol_selector import (
    AssessmentProtocolCandidate,
    AssessmentProtocolSelection,
    AssessmentSelectionContext,
    build_assessment_selection_context,
    select_assessment_protocol,
)
from opencoach.planning.assessment.safety import (
    AssessmentSafetyContext,
    build_assessment_safety_context,
)
from opencoach.planning.assessment.recommendation import (
    AssessmentPlanRecommendation,
    AssessmentRecommendationStatus,
    build_assessment_recommendation,
)
from opencoach.planning.assessment.consolidation import (
    ConsolidatedAssessmentPlan,
    consolidate_assessment_needs,
)
from opencoach.planning.assessment.session import (
    AssessmentSessionSpec,
    build_assessment_session_spec,
)
from opencoach.planning.assessment.session_placement import (
    build_assessment_training_session,
    place_assessment_session,
)
from opencoach.planning.assessment.placement_proposal import (
    AssessmentPlacementProposal,
    AssessmentPlacementStatus,
    build_assessment_placement_proposal,
)
from opencoach.planning.assessment.placement_apply import (
    AssessmentPlacementApplication,
    AssessmentPlacementApplyError,
    apply_assessment_placement,
)
from opencoach.planning.assessment.planning_service import (
    AssessmentPlanningError,
    AssessmentPlanningService,
)
from opencoach.planning.season.strategy import (
    MacrocyclePhase,
    MacrocyclePhaseType,
    SeasonStrategy,
    StrategyRevision,
    StrategyRevisionReason,
    TrainingStimulus,
    TrainingStimulusType,
    TrajectoryStatus,
    WeekTrajectory,
)
from opencoach.planning.season.planning_input import (
    SeasonAthleteContext,
    SeasonConstraintContext,
    SeasonGoalContext,
    SeasonKnowledgeContext,
    SeasonPlanningInput,
    SeasonTrainingState,
)
from opencoach.planning.season.strategy_proposal import (
    AssumptionImpact,
    SeasonStrategyProposal,
    StrategyAssumption,
    StrategyChangeAction,
    StrategyDecision,
    StrategyDecisionType,
    StrategyFactReference,
    StrategyRevisionChange,
    StrategyUncertainty,
    UncertaintyLevel,
)
from opencoach.planning.season.strategy_validator import (
    SeasonStrategyValidation,
    StrategyViolation,
    ViolationSeverity,
    validate_season_strategy_proposal,
)
from opencoach.planning.season.policy import (
    PolicyAuthority,
    PolicyCategory,
    PolicySource,
    PolicySourceType,
    SeasonPlanningPolicy,
    SeasonPolicyRule,
)
from opencoach.planning.season.policy_parameters import (
    AbsoluteLoadLimitParameters,
    AssessmentTimingParameters,
    ComparisonOperator,
    PolicyParameters,
    RaceProximityParameters,
    RecoverySpacingParameters,
    RelativeLoadLimitParameters,
    TaperParameters,
)
from opencoach.planning.season.policy_evaluation import (
    PolicyEvaluationStatus,
    PolicyRuleEvaluation,
    SeasonPolicyEvaluation,
)
from opencoach.planning.season.policy_evaluators import (
    evaluate_policy_rule,
)
from opencoach.planning.season.policy_evaluator import (
    evaluate_season_policy,
)
from opencoach.planning.season.strategy_gate import (
    SeasonStrategyGateResult,
    SeasonStrategyGateStatus,
    evaluate_season_strategy_gate,
)
from opencoach.planning.knowledge.training import (
    KnowledgeApplicability,
    KnowledgeEvidenceLevel,
    KnowledgeSourceType,
    KnowledgeTopic,
    TrainingKnowledgeBase,
    TrainingKnowledgeItem,
    TrainingKnowledgeSource,
)
from opencoach.planning.knowledge.selection import (
    TrainingKnowledgeSelection,
    select_training_knowledge,
)
from opencoach.planning.knowledge.requirements import (
    KnowledgeRequirementReason,
    TrainingKnowledgeRequirements,
    infer_training_knowledge_requirements,
)
from opencoach.planning.knowledge.race_classification import (
    RaceClassificationThresholds,
    RaceDistanceFamily,
    RaceElevationProfile,
    RaceKnowledgeClassification,
    RaceSportFamily,
    classify_race_for_knowledge,
)
from opencoach.planning.knowledge.context import (
    TrainingKnowledgeContext,
    build_training_knowledge_context,
)
from opencoach.planning.season.strategist_context import (
    SeasonStrategistContext,
    build_season_strategist_context,
)
from opencoach.planning.season.strategist_request import (
    SeasonStrategistRequest,
    build_season_strategist_request,
)
from opencoach.planning.season.strategist_port import (
    SeasonStrategistError,
    SeasonStrategistInvalidResponseError,
    SeasonStrategistPort,
    SeasonStrategistResponse,
    SeasonStrategistUnavailableError,
)
from opencoach.planning.season.fake_strategist import (
    FakeSeasonStrategist,
)
from opencoach.planning.season.strategy_schema import (
    build_season_strategy_proposal_schema,
)
from opencoach.planning.season.strategy_parser import (
    parse_season_strategy_proposal,
)
from opencoach.planning.season.strategist_service import (
    SeasonStrategistExecution,
    SeasonStrategistService,
)

__all__ = [
    "DayAvailability",
    "DayAvailabilityStatus",
    "PlanningContext",
    "PlanningContextAssessment",
    "PlanningContextService",
    "assess_planning_context",
    "resolve_day_availability",
    "WeeklyAvailability",
    "build_weekly_availability",
    "TrainingDayCandidate",
    "rank_training_day_candidates",
    "SessionPlacementContext",
    "build_session_placement_context",
    "SessionPlacementCandidate",
    "rank_session_placement_candidates",
    "PlacementRuleResult",
    "RuleSeverity",
    "evaluate_placement_rules",
    "SessionPlacementResult",
    "build_session_placement_result",
    "TrainingHistorySnapshot",
    "TrainingHistorySnapshotService",
    "TrainingHistoryMetrics",
    "WeeklyTrainingAverages",
    "calculate_training_history_metrics",
    "AthleteCapacityAssessment",
    "CapacityConfidence",
    "assess_athlete_capacity",
    "CapacityMetricComparison",
    "CapacityProfileComparison",
    "ComparisonStatus",
    "compare_capacity_to_profile",
    "AthleteTrainingBaseline",
    "build_training_baseline",
    "CalibrationStatus",
    "PhysiologicalCalibrationAssessment",
    "PhysiologicalMetricAssessment",
    "assess_physiological_calibration",
    "MeasurementFreshness",
    "PhysiologicalFreshnessAssessment",
    "PhysiologicalFreshnessPolicy",
    "assess_measurement_freshness",
    "CalibrationMetricSource",
    "PhysiologicalCalibrationMetric",
    "PhysiologicalCalibrationSnapshot",
    "PhysiologicalCalibrationSnapshotService",
    "AssessmentNeed",
    "AssessmentPriority",
    "AssessmentType",
    "identify_assessment_needs",
    "ASSESSMENT_PROTOCOLS",
    "AssessmentProtocol",
    "ProtocolEnvironment",
    "ProtocolIntensity",
    "get_assessment_protocol",
    "get_assessment_protocols",
    "AssessmentProtocolCandidate",
    "AssessmentProtocolSelection",
    "AssessmentSelectionContext",
    "select_assessment_protocol",
    "AssessmentSafetyContext",
    "build_assessment_safety_context",
    "build_assessment_selection_context",
    "AssessmentPlanRecommendation",
    "AssessmentRecommendationStatus",
    "build_assessment_recommendation",
    "ConsolidatedAssessmentPlan",
    "consolidate_assessment_needs",
    "AssessmentSessionSpec",
    "build_assessment_session_spec",
    "build_assessment_training_session",
    "place_assessment_session",
    "AssessmentPlacementProposal",
    "AssessmentPlacementStatus",
    "build_assessment_placement_proposal",
    "AssessmentPlacementApplication",
    "AssessmentPlacementApplyError",
    "apply_assessment_placement",
    "AssessmentPlanningError",
    "AssessmentPlanningService",
    "MacrocyclePhase",
    "MacrocyclePhaseType",
    "SeasonStrategy",
    "StrategyRevision",
    "StrategyRevisionReason",
    "TrainingStimulus",
    "TrainingStimulusType",
    "TrajectoryStatus",
    "WeekTrajectory",
    "SeasonAthleteContext",
    "SeasonConstraintContext",
    "SeasonGoalContext",
    "SeasonKnowledgeContext",
    "SeasonPlanningInput",
    "SeasonTrainingState",
    "AssumptionImpact",
    "SeasonStrategyProposal",
    "StrategyAssumption",
    "StrategyChangeAction",
    "StrategyDecision",
    "StrategyDecisionType",
    "StrategyFactReference",
    "StrategyRevisionChange",
    "StrategyUncertainty",
    "UncertaintyLevel",
    "SeasonStrategyValidation",
    "StrategyViolation",
    "ViolationSeverity",
    "validate_season_strategy_proposal",
    "PolicyAuthority",
    "PolicyCategory",
    "PolicySource",
    "PolicySourceType",
    "SeasonPlanningPolicy",
    "SeasonPolicyRule",
    "AbsoluteLoadLimitParameters",
    "AssessmentTimingParameters",
    "ComparisonOperator",
    "PolicyParameters",
    "RaceProximityParameters",
    "RecoverySpacingParameters",
    "RelativeLoadLimitParameters",
    "TaperParameters",
    "PolicyEvaluationStatus",
    "PolicyRuleEvaluation",
    "SeasonPolicyEvaluation",
    "evaluate_policy_rule",
    "evaluate_season_policy",
    "SeasonStrategyGateResult",
    "SeasonStrategyGateStatus",
    "evaluate_season_strategy_gate",
    "KnowledgeApplicability",
    "KnowledgeEvidenceLevel",
    "KnowledgeSourceType",
    "KnowledgeTopic",
    "TrainingKnowledgeBase",
    "TrainingKnowledgeItem",
    "TrainingKnowledgeSource",
    "TrainingKnowledgeSelection",
    "select_training_knowledge",
    "KnowledgeRequirementReason",
    "TrainingKnowledgeRequirements",
    "infer_training_knowledge_requirements",
    "RaceClassificationThresholds",
    "RaceDistanceFamily",
    "RaceElevationProfile",
    "RaceKnowledgeClassification",
    "RaceSportFamily",
    "classify_race_for_knowledge",
    "TrainingKnowledgeContext",
    "build_training_knowledge_context",
    "SeasonStrategistContext",
    "build_season_strategist_context",
    "SeasonStrategistRequest",
    "build_season_strategist_request",
    "SeasonStrategistError",
    "SeasonStrategistInvalidResponseError",
    "SeasonStrategistPort",
    "SeasonStrategistUnavailableError",
    "FakeSeasonStrategist",
    "SeasonStrategistResponse",
    "build_season_strategy_proposal_schema",
    "parse_season_strategy_proposal",
    "SeasonStrategistExecution",
    "SeasonStrategistService",
]
