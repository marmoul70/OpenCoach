import pytest

from opencoach.planning.sessions.coach_port import (
    SessionCoachRequest,
)
from opencoach.planning.sessions.intent import (
    build_session_intent,
)
from opencoach.planning.sessions.proposal import (
    SessionBlock,
    SessionProposal,
)
from opencoach.planning.sessions.proposal_validator import (
    SessionProposalValidationIssue,
    SessionProposalValidationResult,
    SessionProposalViolation,
    validate_session_proposal,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.weekly.schedule_types import (
    FatigueBudget,
    Weekday,
)
from opencoach.planning.weekly.session_intent_slot import (
    WeeklySessionIntentSlot,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def create_request(
    *,
    minimum: int | None = 120,
    maximum: int | None = 180,
    available: int | None = 180,
    secondary: tuple[
        TrainingStimulusRequirement,
        ...
    ] = (),
) -> SessionCoachRequest:
    primary = TrainingStimulusRequirement(
        stimulus=(
            TrainingStimulus.LONG_ENDURANCE
        ),
        priority=StimulusPriority.KEY,
        specificity=SpecificityLevel.HIGH,
        substitution=SubstitutionPolicy.FORBIDDEN,
        preferred_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
        duration_min_minutes=minimum,
        duration_max_minutes=maximum,
    )

    intent = build_session_intent(
        primary=primary,
        secondary=secondary,
    )

    slot = WeeklySessionIntentSlot(
        slot_id="long-trail",
        day=Weekday.SUNDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.HIGH,
        duration_available_minutes=available,
    )

    return SessionCoachRequest(
        phase=TrainingPhase.SPECIFIC,
        slot=slot,
        target_load=500.0,
    )


def create_secondary_requirement(
    stimulus: TrainingStimulus,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=stimulus,
        priority=StimulusPriority.IMPORTANT,
        specificity=SpecificityLevel.HIGH,
        substitution=SubstitutionPolicy.FORBIDDEN,
        preferred_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
    )


def create_proposal(
    *,
    duration: int = 150,
    modality: TrainingModality = (
        TrainingModality.TRAIL_RUNNING
    ),
    stimuli: tuple[
        TrainingStimulus,
        ...
    ] = (
        TrainingStimulus.LONG_ENDURANCE,
    ),
) -> SessionProposal:
    return SessionProposal(
        title="Sortie longue trail",
        modality=modality,
        duration_minutes=duration,
        covered_stimuli=stimuli,
        blocks=(
            SessionBlock(
                name="Séance",
                description=(
                    "Sortie longue trail spécifique."
                ),
                duration_minutes=duration,
            ),
        ),
        objective=(
            "Développer l'endurance spécifique."
        ),
    )


def test_valid_proposal_is_accepted() -> None:
    result = validate_session_proposal(
        request=create_request(),
        proposal=create_proposal(),
    )

    assert result.valid is True

    assert result.issues == ()

    assert result.violations == ()


def test_duration_below_minimum_is_rejected() -> None:
    result = validate_session_proposal(
        request=create_request(
            minimum=120,
        ),
        proposal=create_proposal(
            duration=100,
        ),
    )

    assert result.valid is False

    assert (
        SessionProposalViolation
        .DURATION_BELOW_MINIMUM
        in result.violations
    )


def test_duration_above_maximum_is_rejected() -> None:
    result = validate_session_proposal(
        request=create_request(
            maximum=150,
            available=180,
        ),
        proposal=create_proposal(
            duration=160,
        ),
    )

    assert (
        SessionProposalViolation
        .DURATION_ABOVE_MAXIMUM
        in result.violations
    )


def test_duration_above_availability_is_rejected() -> None:
    result = validate_session_proposal(
        request=create_request(
            maximum=180,
            available=140,
            minimum=120,
        ),
        proposal=create_proposal(
            duration=150,
        ),
    )

    assert (
        SessionProposalViolation
        .DURATION_ABOVE_AVAILABILITY
        in result.violations
    )


def test_duration_can_generate_multiple_violations() -> None:
    result = validate_session_proposal(
        request=create_request(
            minimum=60,
            maximum=120,
            available=100,
        ),
        proposal=create_proposal(
            duration=150,
        ),
    )

    assert result.valid is False

    assert (
        SessionProposalViolation
        .DURATION_ABOVE_MAXIMUM
        in result.violations
    )

    assert (
        SessionProposalViolation
        .DURATION_ABOVE_AVAILABILITY
        in result.violations
    )


def test_required_modality_is_enforced() -> None:
    result = validate_session_proposal(
        request=create_request(),
        proposal=create_proposal(
            modality=(
                TrainingModality.CYCLING
            ),
        ),
    )

    assert (
        SessionProposalViolation
        .REQUIRED_MODALITY_NOT_RESPECTED
        in result.violations
    )


def test_primary_stimulus_is_required() -> None:
    result = validate_session_proposal(
        request=create_request(),
        proposal=create_proposal(
            stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
        ),
    )

    assert (
        SessionProposalViolation
        .PRIMARY_STIMULUS_MISSING
        in result.violations
    )


def test_secondary_stimulus_is_required() -> None:
    uphill = create_secondary_requirement(
        TrainingStimulus.UPHILL_STRENGTH
    )

    request = create_request(
        secondary=(
            uphill,
        )
    )

    proposal = create_proposal(
        stimuli=(
            TrainingStimulus.LONG_ENDURANCE,
        )
    )

    result = validate_session_proposal(
        request=request,
        proposal=proposal,
    )

    assert (
        SessionProposalViolation
        .SECONDARY_STIMULUS_MISSING
        in result.violations
    )


def test_all_stimuli_can_be_covered() -> None:
    uphill = create_secondary_requirement(
        TrainingStimulus.UPHILL_STRENGTH
    )

    downhill = create_secondary_requirement(
        TrainingStimulus.DOWNHILL_SPECIFICITY
    )

    request = create_request(
        secondary=(
            uphill,
            downhill,
        )
    )

    proposal = create_proposal(
        stimuli=(
            TrainingStimulus.LONG_ENDURANCE,
            TrainingStimulus.UPHILL_STRENGTH,
            TrainingStimulus.DOWNHILL_SPECIFICITY,
        )
    )

    result = validate_session_proposal(
        request=request,
        proposal=proposal,
    )

    assert result.valid is True


def test_extra_stimulus_is_not_rejected() -> None:
    proposal = create_proposal(
        stimuli=(
            TrainingStimulus.LONG_ENDURANCE,
            TrainingStimulus.AEROBIC_EASY,
        )
    )

    result = validate_session_proposal(
        request=create_request(),
        proposal=proposal,
    )

    assert result.valid is True


def test_no_duration_limits_accepts_positive_duration() -> None:
    request = create_request(
        minimum=None,
        maximum=None,
        available=None,
    )

    proposal = create_proposal(
        duration=240,
    )

    result = validate_session_proposal(
        request=request,
        proposal=proposal,
    )

    assert result.valid is True


def test_valid_result_cannot_contain_issues() -> None:
    issue = SessionProposalValidationIssue(
        violation=(
            SessionProposalViolation
            .PRIMARY_STIMULUS_MISSING
        ),
        message="Stimulus absent.",
    )

    with pytest.raises(
        ValueError,
        match="valide",
    ):
        SessionProposalValidationResult(
            valid=True,
            issues=(
                issue,
            ),
        )


def test_invalid_result_requires_issue() -> None:
    with pytest.raises(
        ValueError,
        match="au moins une violation",
    ):
        SessionProposalValidationResult(
            valid=False,
            issues=(),
        )


def test_validation_issue_requires_message() -> None:
    with pytest.raises(
        ValueError,
        match="message",
    ):
        SessionProposalValidationIssue(
            violation=(
                SessionProposalViolation
                .PRIMARY_STIMULUS_MISSING
            ),
            message=" ",
        )
