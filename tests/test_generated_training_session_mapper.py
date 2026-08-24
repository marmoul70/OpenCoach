from datetime import date

from opencoach.coaching.generation.mapper import (
    generated_session_to_training_session,
)
from opencoach.coaching.generation.models import (
    GeneratedTrainingSession,
)
from opencoach.planning.sessions.generators import (
    DeterministicSessionGenerator,
)
from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.sessions.coach_port import (
    SessionCoachRequest,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
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


def create_generated_session():
    intent = SessionIntent(
        primary_stimulus=(
            TrainingStimulus.THRESHOLD
        ),
        secondary_stimuli=(),
        importance=(
            SessionIntentImportance.IMPORTANT
        ),
        specificity=SpecificityLevel.HIGH,
        substitution=(
            SubstitutionPolicy.ALLOWED
        ),
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        required_modalities=(),
        duration_min_minutes=70,
        duration_max_minutes=70,
    )

    slot = WeeklySessionIntentSlot(
        slot_id="threshold",
        day=Weekday.WEDNESDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.HIGH,
        duration_available_minutes=70,
    )

    proposal = (
        DeterministicSessionGenerator()
        .generate_session(
            request=SessionCoachRequest(
                phase=TrainingPhase.SPECIFIC,
                slot=slot,
            )
        )
    )

    return GeneratedTrainingSession(
        slot_id="threshold",
        date=date(
            2027,
            7,
            7,
        ),
        day=Weekday.WEDNESDAY,
        phase=TrainingPhase.SPECIFIC,
        proposal=proposal,
    )


def test_maps_generated_session_to_training_session() -> None:
    generated = (
        create_generated_session()
    )

    session = (
        generated_session_to_training_session(
            generated,
            planning_key=(
                "2027-07-05:threshold"
            ),
        )
    )

    assert session.id is None
    assert session.date == generated.date

    assert (
        session.planning_key
        == "2027-07-05:threshold"
    )

    assert (
        session.type
        == "threshold"
    )

    assert (
        session.sport_type
        == "Run"
    )

    assert (
        session.title
        == "Travail au seuil"
    )

    assert session.duration_minutes == 70
    assert session.status == "planned"


def test_mapper_preserves_existing_identifier() -> None:
    from uuid import uuid4

    session_id = uuid4()

    session = (
        generated_session_to_training_session(
            create_generated_session(),
            planning_key=(
                "2027-07-05:threshold"
            ),
            existing_id=session_id,
        )
    )

    assert session.id == session_id

def test_description_contains_session_blocks() -> None:
    session = (
        generated_session_to_training_session(
            create_generated_session(),
            planning_key=(
                "2027-07-05:threshold"
            ),
        )
    )

    assert "Échauffement" in (
        session.description
    )

    assert "Bloc seuil" in (
        session.description
    )

def test_mapper_preserves_planning_key() -> None:
    session = (
        generated_session_to_training_session(
            create_generated_session(),
            planning_key=(
                "2027-07-05:threshold"
            ),
        )
    )

    assert (
        session.planning_key
        == "2027-07-05:threshold"
    )