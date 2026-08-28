from datetime import date
from uuid import uuid4

from opencoach.physiology.testing import (
    PhysiologicalMetric,
    PhysiologicalTestPlanningStatus,
    PhysiologicalTestProposal,
    PhysiologicalTestReplacementStimulus,
    PhysiologicalTestType,
    plan_physiological_test_in_week,
    select_test_target_session,
)
from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
)


TEST_DATE = date(
    2026,
    9,
    9,
)


def intent(
    stimulus: TrainingStimulus,
    *,
    importance: SessionIntentImportance = (
        SessionIntentImportance.IMPORTANT
    ),
) -> SessionIntent:
    return SessionIntent(
        primary_stimulus=stimulus,
        secondary_stimuli=(),
        importance=importance,
        specificity=(
            SpecificityLevel.MODERATE
        ),
        substitution=(
            SubstitutionPolicy.ALLOWED
        ),
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        required_modalities=(),
    )


def proposal(
    *,
    replacement: (
        PhysiologicalTestReplacementStimulus
    ) = (
        PhysiologicalTestReplacementStimulus
        .AEROBIC_POWER
    ),
) -> PhysiologicalTestProposal:
    return PhysiologicalTestProposal(
        athlete_profile_id=uuid4(),
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        target_metrics=(
            PhysiologicalMetric.VMA,
        ),
        proposed_date=TEST_DATE,
        reason="VMA à recalibrer.",
        recommendation=(
            "OpenCoach recommande un test."
        ),
        replacement_stimulus=replacement,
    )


def test_pending_test_does_not_replace_session_yet() -> None:
    result = (
        plan_physiological_test_in_week(
            proposal=proposal(),
            intents=(
                intent(
                    TrainingStimulus.AEROBIC_EASY
                ),
                intent(
                    TrainingStimulus.VO2MAX
                ),
            ),
        )
    )

    assert (
        result.status
        is PhysiologicalTestPlanningStatus
        .AWAITING_ATHLETE
    )

    assert (
        result.original_session_should_remain
        is True
    )

    assert result.session_count_delta == 0


def test_accepted_vma_test_replaces_vo2_session() -> None:
    accepted = (
        proposal()
        .accept()
    )

    result = (
        plan_physiological_test_in_week(
            proposal=accepted,
            intents=(
                intent(
                    TrainingStimulus.AEROBIC_EASY
                ),
                intent(
                    TrainingStimulus.VO2MAX
                ),
                intent(
                    TrainingStimulus.LONG_ENDURANCE
                ),
            ),
        )
    )

    assert (
        result.status
        is PhysiologicalTestPlanningStatus
        .TEST_REPLACES_SESSION
    )

    assert result.target is not None

    assert (
        result.target.intent.primary_stimulus
        is TrainingStimulus.VO2MAX
    )

    assert (
        result.test_should_replace_session
        is True
    )

    assert result.session_count_delta == 0


def test_declined_test_keeps_quality_session() -> None:
    declined = (
        proposal()
        .decline()
    )

    result = (
        plan_physiological_test_in_week(
            proposal=declined,
            intents=(
                intent(
                    TrainingStimulus.VO2MAX
                ),
            ),
        )
    )

    assert (
        result.status
        is PhysiologicalTestPlanningStatus
        .ORIGINAL_SESSION_KEPT
    )

    assert (
        result.original_session_should_remain
        is True
    )

    assert result.session_count_delta == 0


def test_vma_prefers_vo2_over_threshold() -> None:
    target = (
        select_test_target_session(
            proposal=proposal(),
            intents=(
                intent(
                    TrainingStimulus.THRESHOLD
                ),
                intent(
                    TrainingStimulus.VO2MAX
                ),
            ),
        )
    )

    assert target is not None

    assert (
        target.intent.primary_stimulus
        is TrainingStimulus.VO2MAX
    )


def test_threshold_test_replaces_threshold_session() -> None:
    threshold_proposal = (
        PhysiologicalTestProposal(
            athlete_profile_id=uuid4(),
            protocol=(
                PhysiologicalTestType
                .THRESHOLD_20_MIN
            ),
            target_metrics=(
                PhysiologicalMetric
                .THRESHOLD_HEART_RATE,
            ),
            proposed_date=TEST_DATE,
            reason="Seuil à recalibrer.",
            recommendation=(
                "Test seuil recommandé."
            ),
            replacement_stimulus=(
                PhysiologicalTestReplacementStimulus
                .THRESHOLD
            ),
        )
        .accept()
    )

    result = (
        plan_physiological_test_in_week(
            proposal=threshold_proposal,
            intents=(
                intent(
                    TrainingStimulus.VO2MAX
                ),
                intent(
                    TrainingStimulus.THRESHOLD
                ),
            ),
        )
    )

    assert result.target is not None

    assert (
        result.target.intent.primary_stimulus
        is TrainingStimulus.THRESHOLD
    )


def test_uphill_test_prefers_uphill_quality() -> None:
    uphill = (
        PhysiologicalTestProposal(
            athlete_profile_id=uuid4(),
            protocol=(
                PhysiologicalTestType.UPHILL_6_MIN
            ),
            target_metrics=(
                PhysiologicalMetric.UPHILL_VAM,
            ),
            proposed_date=TEST_DATE,
            reason="Profil montée à calibrer.",
            recommendation=(
                "Test montée recommandé."
            ),
            replacement_stimulus=(
                PhysiologicalTestReplacementStimulus
                .UPHILL_INTENSITY
            ),
        )
        .accept()
    )

    result = (
        plan_physiological_test_in_week(
            proposal=uphill,
            intents=(
                intent(
                    TrainingStimulus.THRESHOLD
                ),
                intent(
                    TrainingStimulus.UPHILL_THRESHOLD
                ),
            ),
        )
    )

    assert result.target is not None

    assert (
        result.target.intent.primary_stimulus
        is TrainingStimulus.UPHILL_THRESHOLD
    )


def test_test_is_not_added_when_no_quality_session_exists() -> None:
    accepted = (
        proposal()
        .accept()
    )

    result = (
        plan_physiological_test_in_week(
            proposal=accepted,
            intents=(
                intent(
                    TrainingStimulus.AEROBIC_EASY
                ),
                intent(
                    TrainingStimulus.LONG_ENDURANCE
                ),
            ),
        )
    )

    assert (
        result.status
        is PhysiologicalTestPlanningStatus
        .NO_COMPATIBLE_SESSION
    )

    assert result.target is None

    assert result.session_count_delta == 0


def test_more_important_compatible_session_wins() -> None:
    target = (
        select_test_target_session(
            proposal=proposal(),
            intents=(
                intent(
                    TrainingStimulus.VO2MAX,
                    importance=(
                        SessionIntentImportance
                        .IMPORTANT
                    ),
                ),
                intent(
                    TrainingStimulus.VO2MAX,
                    importance=(
                        SessionIntentImportance.KEY
                    ),
                ),
            ),
        )
    )

    assert target is not None

    assert target.intent_index == 1
