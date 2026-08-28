"""Tests physiologiques OpenCoach."""

from opencoach.physiology.testing.catalog import (
    PHYSIOLOGICAL_TEST_CATALOG,
    get_test_protocol,
    list_test_protocols_for_disciplines,
    list_test_protocols_for_metric,
)
from opencoach.physiology.testing.models import (
    ActivityMetric,
    EvidenceLevel,
    PhysiologicalMetric,
    PhysiologicalTestProtocol,
    PhysiologicalTestType,
    SportDiscipline,
    PhysiologicalTestAcquisitionMode,
    PhysiologicalTestEffortLevel,
    PhysiologicalTestFatigueCost,
)

__all__ = [
    "ActivityMetric",
    "EvidenceLevel",
    "PHYSIOLOGICAL_TEST_CATALOG",
    "PhysiologicalMetric",
    "PhysiologicalTestProtocol",
    "PhysiologicalTestType",
    "SportDiscipline",
    "PhysiologicalTestAcquisitionMode",
    "PhysiologicalTestEffortLevel",
    "PhysiologicalTestFatigueCost",
    "get_test_protocol",
    "list_test_protocols_for_disciplines",
    "list_test_protocols_for_metric",
]

from opencoach.physiology.testing.proposal import (
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
    PhysiologicalTestReplacementStimulus,
)
from opencoach.physiology.testing.proposal_service import (
    PhysiologicalTestProposalRequest,
    propose_physiological_test,
)
from opencoach.physiology.testing.replacement import (
    get_test_replacement_stimulus,
)

__all__ += [
    "PhysiologicalTestDecision",
    "PhysiologicalTestProposal",
    "PhysiologicalTestProposalRequest",
    "PhysiologicalTestReplacementStimulus",
    "get_test_replacement_stimulus",
    "propose_physiological_test",
]

from opencoach.physiology.testing.decision import (
    DECLINED_TEST_COOLDOWN_DAYS,
    PhysiologicalTestNeedDecision,
    PhysiologicalTestNeedRequest,
    PreviousTestDecision,
    PhysiologicalTestingSeasonPhase,
    PhysiologicalTestNeedStatus,
    evaluate_physiological_test_need,
)
from opencoach.physiology.testing.freshness import (
    MeasurementConfidence,
    MeasurementFreshness,
    MeasurementFreshnessPolicy,
    PhysiologicalMeasurementEvidence,
    evaluate_measurement_freshness,
    get_measurement_freshness_policy,
)

__all__ += [
    "DECLINED_TEST_COOLDOWN_DAYS",
    "MeasurementConfidence",
    "MeasurementFreshness",
    "MeasurementFreshnessPolicy",
    "PhysiologicalMeasurementEvidence",
    "PhysiologicalTestNeedDecision",
    "PhysiologicalTestNeedRequest",
    "PreviousTestDecision",
    "PhysiologicalTestingSeasonPhase",
    "PhysiologicalTestNeedStatus",
    "evaluate_measurement_freshness",
    "evaluate_physiological_test_need",
    "get_measurement_freshness_policy",
]

from opencoach.physiology.testing.planning import (
    PhysiologicalTestPlanningDecision,
    PhysiologicalTestPlanningStatus,
    PhysiologicalTestSessionTarget,
    plan_physiological_test_in_week,
    select_test_target_session,
)

__all__ += [
    "PhysiologicalTestPlanningDecision",
    "PhysiologicalTestPlanningStatus",
    "PhysiologicalTestSessionTarget",
    "plan_physiological_test_in_week",
    "select_test_target_session",
]

from opencoach.physiology.testing.session import (
    PhysiologicalTestSegmentIntensity,
    PhysiologicalTestSegmentType,
    PhysiologicalTestSession,
    PhysiologicalTestSessionSegment,
)
from opencoach.physiology.testing.session_generator import (
    generate_physiological_test_session,
)

__all__ += [
    "PhysiologicalTestSegmentIntensity",
    "PhysiologicalTestSegmentType",
    "PhysiologicalTestSession",
    "PhysiologicalTestSessionSegment",
    "generate_physiological_test_session",
]

from opencoach.physiology.testing.application import (
    ApplyPhysiologicalTestDecisionService,
    PhysiologicalTestApplicationError,
    PhysiologicalTestApplicationResult,
    PhysiologicalTestApplicationStatus,
)

__all__ += [
    "ApplyPhysiologicalTestDecisionService",
    "PhysiologicalTestApplicationError",
    "PhysiologicalTestApplicationResult",
    "PhysiologicalTestApplicationStatus",
]

