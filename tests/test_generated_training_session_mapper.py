from dataclasses import replace
from datetime import date

from opencoach.planning.sessions.prescription import (
    IntensityRange,
    IntensityReference,
    SessionIntensityPrescription,
)

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

def test_mapper_persists_canonical_intensity() -> None:
    session = (
        generated_session_to_training_session(
            create_generated_session(),
            planning_key=(
                "2027-07-05:threshold"
            ),
        )
    )

    assert session.intensity == "hard"


def test_mapper_persists_vma_speed_and_pace_targets() -> None:
    generated = create_generated_session()

    vma_target = IntensityRange(
        reference=(
            IntensityReference.VMA_PERCENT
        ),
        minimum=60.0,
        maximum=70.0,
        unit="% VMA",
        label="Pourcentage de VMA",
    )

    rpe_target = IntensityRange(
        reference=(
            IntensityReference.RPE
        ),
        minimum=2.0,
        maximum=3.0,
        unit="/10",
        label="Perception de l'effort",
    )

    prescription = (
        SessionIntensityPrescription(
            stimulus=(
                generated.proposal
                .covered_stimuli[0]
            ),
            primary_target=(
                vma_target
            ),
            secondary_targets=(
                rpe_target,
            ),
        )
    )

    proposal = replace(
        generated.proposal,
        intensity_prescription=(
            prescription
        ),
    )

    generated = replace(
        generated,
        proposal=proposal,
        vma_kmh=15.0,
    )

    mapped = (
        generated_session_to_training_session(
            generated,
            planning_key=(
                "test-vma-targets"
            ),
        )
    )

    assert mapped.prescription is not None

    intensity = mapped.prescription[
        "intensity"
    ]

    assert intensity is not None

    persisted_vma_target = next(
        target
        for target
        in intensity["targets"]
        if (
            target["reference"]
            == "vma_percent"
        )
    )

    assert (
        persisted_vma_target[
            "minimum"
        ]
        == 60.0
    )

    assert (
        persisted_vma_target[
            "maximum"
        ]
        == 70.0
    )

    derived = persisted_vma_target[
        "derived"
    ]

    assert (
        derived["vma_kmh"]
        == 15.0
    )

    assert (
        derived["speed_kmh"][
            "minimum"
        ]
        == 9.0
    )

    assert (
        derived["speed_kmh"][
            "maximum"
        ]
        == 10.5
    )

    assert (
        derived[
            "pace_seconds_per_km"
        ]["slowest"]
        == 400.0
    )

    assert round(
        derived[
            "pace_seconds_per_km"
        ]["fastest"],
    ) == 343
