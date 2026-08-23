import pytest

from opencoach.planning.sessions.coach_port import (
    SessionCoachPort,
    SessionCoachRequest,
)
from opencoach.planning.sessions.intent import (
    build_session_intent,
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


def create_slot() -> WeeklySessionIntentSlot:
    requirement = TrainingStimulusRequirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
        specificity=SpecificityLevel.LOW,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        duration_min_minutes=30,
        duration_max_minutes=60,
    )

    intent = build_session_intent(
        primary=requirement,
    )

    return WeeklySessionIntentSlot(
        slot_id="easy-monday",
        day=Weekday.MONDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.LOW,
        duration_available_minutes=60,
    )


def test_session_coach_request_accepts_valid_context() -> None:
    request = SessionCoachRequest(
        phase=TrainingPhase.BASE,
        slot=create_slot(),
        target_load=300.0,
        athlete_context=(
            "Athlète trail, niveau intermédiaire."
        ),
        additional_context=(
            "Terrain vallonné disponible.",
        ),
    )

    assert request.phase is TrainingPhase.BASE
    assert request.target_load == 300.0


def test_negative_target_load_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="charge cible",
    ):
        SessionCoachRequest(
            phase=TrainingPhase.BASE,
            slot=create_slot(),
            target_load=-1.0,
        )


def test_empty_athlete_context_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="contexte athlète",
    ):
        SessionCoachRequest(
            phase=TrainingPhase.BASE,
            slot=create_slot(),
            athlete_context=" ",
        )


def test_protocol_is_runtime_checkable() -> None:
    class MinimalCoach:
        def generate_session(
            self,
            *,
            request: SessionCoachRequest,
        ):
            raise NotImplementedError

    assert isinstance(
        MinimalCoach(),
        SessionCoachPort,
    )
