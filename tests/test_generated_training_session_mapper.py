from dataclasses import replace
from datetime import date
from uuid import uuid4

from opencoach.planning.sessions.prescription import (
    IntensityRange,
    IntensityReference,
    SessionIntensityPrescription,
)

from opencoach.integrations.coros.workout_mapper import (
    map_training_session_to_coros,
)
from opencoach.planning.sessions.prescription.integrity import (
    validate_training_session_prescription,
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


def create_generated_session(*, secondary_stimuli=()):
    intent = SessionIntent(
        primary_stimulus=(
            TrainingStimulus.THRESHOLD
        ),
        secondary_stimuli=secondary_stimuli,
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


def test_mapper_persists_phase_metadata_and_block_level_intensity() -> None:
    generated = create_generated_session()
    mapped = generated_session_to_training_session(
        generated,
        planning_key="phase-metadata",
    )

    assert mapped.prescription is not None
    assert mapped.prescription["version"] == 2
    blocks = mapped.prescription["blocks"]
    phases = [block["phase"] for block in blocks]

    assert "warmup" in phases
    assert "main" in phases
    assert "cooldown" in phases

    recovery_intensity = mapped.prescription["recovery_intensity"]
    assert recovery_intensity is not None
    assert recovery_intensity["targets"]

    main_block = next(block for block in blocks if block["phase"] == "main")
    assert main_block["intensity"] is not None
    assert main_block["intensity"]["targets"]
    warmup_block = next(block for block in blocks if block["phase"] == "warmup")
    assert warmup_block["intensity"] is not None
    assert warmup_block["intensity"]["targets"][0]["reference"] == "rpe"



def test_secondary_stimuli_survive_generation_persistence_validation_and_coros_mapping() -> None:
    generated = create_generated_session(
        secondary_stimuli=(
            TrainingStimulus.UPHILL_THRESHOLD,
            TrainingStimulus.VO2MAX,
        ),
    )
    persisted = generated_session_to_training_session(
        generated,
        planning_key="secondary-stimuli-e2e",
    )

    assert "seuil en montée" in persisted.description.lower()
    assert "puissance aérobie" in persisted.description.lower()

    # Le scénario valide la chaîne de transport du texte secondaire.
    # On fournit une cible FC absolue explicite pour rendre la séance
    # exécutable dans COROS sans convertir arbitrairement le RPE.
    heart_rate_intensity = {
        "targets": [
            {
                "reference": "heart_rate",
                "minimum": 140,
                "maximum": 155,
                "unit": "bpm",
                "label": "Fréquence cardiaque",
            }
        ],
        "guidance": [],
    }
    assert persisted.prescription is not None
    persisted.prescription["intensity"] = heart_rate_intensity
    persisted.prescription["recovery_intensity"] = heart_rate_intensity
    for block in persisted.prescription["blocks"]:
        block["intensity"] = heart_rate_intensity

    validate_training_session_prescription(persisted)
    coros_payload = map_training_session_to_coros(
        replace(persisted, id=uuid4())
    )

    description = coros_payload.course["courseDescription"].lower()
    assert "seuil en montée" in description
    assert "puissance aérobie" in description
    assert coros_payload.course["sections"]


def test_serializes_work_and_recovery_elevation_targets() -> None:
    from opencoach.coaching.generation.mapper import _serialize_work_interval
    from opencoach.planning.sessions.prescription import (
        WorkDurationUnit,
        WorkInterval,
    )

    interval = WorkInterval(
        repetitions=4,
        work_duration=120,
        work_unit=WorkDurationUnit.SECONDS,
        work_elevation_gain_meters=80,
        recovery_duration=60,
        recovery_unit=WorkDurationUnit.SECONDS,
        recovery_distance_meters=100,
    )

    payload = _serialize_work_interval(interval)

    assert payload["work_elevation_gain_meters"] == 80
    assert payload["recovery_distance_meters"] == 100
    assert payload["recovery_elevation_gain_meters"] is None
