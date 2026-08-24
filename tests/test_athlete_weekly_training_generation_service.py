"""Tests du service complet de génération hebdomadaire."""

from datetime import date
from uuid import uuid4

from opencoach.coaching.generation import (
    AthleteWeeklyTrainingGenerationService,
    WeeklyTrainingGenerationService,
)
from opencoach.models import (
    AthleteProfile,
    PhysiologicalMeasurement,
)
from opencoach.planning.physiology.snapshot_service import (
    PhysiologicalCalibrationSnapshotService,
)
from opencoach.planning.sessions.generators import (
    DeterministicSessionGenerator,
)
from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.sessions.prescription import (
    IntensityReference,
    WorkStructureType,
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
    SchedulePressure,
    TrainingPhase,
    WeeklyTrainingEnvelope,
)


REFERENCE_DATE = date(
    2027,
    7,
    5,
)


class FakeProfileRepository:
    """Repository de profil minimal pour le test d'orchestration."""

    def __init__(
        self,
        profile: AthleteProfile,
    ) -> None:
        self.profile = profile

        self.get_calls = 0

    def get_profile(
        self,
    ) -> AthleteProfile:
        self.get_calls += 1

        return self.profile

    def save_profile(
        self,
        profile: AthleteProfile,
    ) -> None:
        self.profile = profile

    def reset_profile(
        self,
    ) -> AthleteProfile:
        self.profile = AthleteProfile()

        return self.profile


class FakeMeasurementRepository:
    """Repository physiologique minimal."""

    def __init__(
        self,
        measurements=(),
    ) -> None:
        self.measurements = tuple(
            measurements
        )

    def get_latest_measurement(
        self,
        athlete_profile_id,
        metric,
    ):
        del athlete_profile_id

        matching = [
            measurement
            for measurement in self.measurements
            if measurement.metric == metric
        ]

        if not matching:
            return None

        return max(
            matching,
            key=lambda measurement: (
                measurement.measured_at
            ),
        )


def create_measurement(
    *,
    metric: str,
    value: float,
) -> PhysiologicalMeasurement:
    """Construit une mesure récente et utilisable."""

    return PhysiologicalMeasurement(
        id=uuid4(),
        metric=metric,
        value=value,
        measured_at=REFERENCE_DATE,
        protocol="integration_test",
        source="field_test",
        confidence="high",
    )


def create_measurements():
    """Calibration physiologique complète de test."""

    return (
        create_measurement(
            metric="vma",
            value=15.0,
        ),
        create_measurement(
            metric="max_heart_rate",
            value=181.0,
        ),
        create_measurement(
            metric="resting_heart_rate",
            value=50.0,
        ),
        create_measurement(
            metric="threshold_heart_rate_1",
            value=145.0,
        ),
        create_measurement(
            metric="threshold_heart_rate_2",
            value=165.0,
        ),
    )


def create_threshold_slot() -> WeeklySessionIntentSlot:
    """Crée une séance seuil de 70 minutes."""

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

    return WeeklySessionIntentSlot(
        slot_id="threshold-wednesday",
        day=Weekday.WEDNESDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.HIGH,
        duration_available_minutes=70,
    )


def create_envelope() -> WeeklyTrainingEnvelope:
    """Crée l'enveloppe de semaine utilisée par les tests."""

    return WeeklyTrainingEnvelope(
        week_start=date(
            2027,
            7,
            5,
        ),
        week_end=date(
            2027,
            7,
            11,
        ),
        phase=TrainingPhase.SPECIFIC,
        target_load=420.0,
        load_min=380.0,
        load_max=460.0,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.SUNDAY,
        ),
        session_slots=(
            create_threshold_slot(),
        ),
        schedule_pressure=(
            SchedulePressure.MODERATE
        ),
    )


def create_service(
    *,
    measurements=None,
):
    """Construit la chaîne réelle de génération."""

    if measurements is None:
        measurements = (
            create_measurements()
        )

    profile_repository = (
        FakeProfileRepository(
            AthleteProfile()
        )
    )

    physiology_service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository(
                measurements
            )
        )
    )

    weekly_generation_service = (
        WeeklyTrainingGenerationService(
            session_generator=(
                DeterministicSessionGenerator()
            )
        )
    )

    service = (
        AthleteWeeklyTrainingGenerationService(
            profile_repository=(
                profile_repository
            ),
            physiology_service=(
                physiology_service
            ),
            generation_service=(
                weekly_generation_service
            ),
        )
    )

    return (
        service,
        profile_repository,
    )


def test_orchestrator_generates_real_week() -> None:
    service, _ = create_service()

    week = service.generate(
        athlete_profile_id=uuid4(),
        envelope=create_envelope(),
        reference_date=REFERENCE_DATE,
    )

    assert week.session_count == 1

    session = week.sessions[0]

    assert (
        session.proposal.title
        == "Travail au seuil"
    )

    assert (
        session.proposal.work_structure
        is not None
    )

    assert (
        session.proposal.work_structure.structure_type
        is WorkStructureType.INTERVALS
    )


def test_orchestrator_uses_physiological_repository() -> None:
    service, _ = create_service()

    week = service.generate(
        athlete_profile_id=uuid4(),
        envelope=create_envelope(),
        reference_date=REFERENCE_DATE,
    )

    prescription = (
        week.sessions[0]
        .proposal
        .intensity_prescription
    )

    assert prescription is not None

    assert (
        prescription.primary_target.reference
        is IntensityReference.HEART_RATE
    )

    assert (
        prescription.primary_target.minimum
        == 157
    )

    assert (
        prescription.primary_target.maximum
        == 165
    )


def test_orchestrator_preserves_vma_reference() -> None:
    service, _ = create_service()

    week = service.generate(
        athlete_profile_id=uuid4(),
        envelope=create_envelope(),
        reference_date=REFERENCE_DATE,
    )

    prescription = (
        week.sessions[0]
        .proposal
        .intensity_prescription
    )

    assert prescription is not None

    vma = prescription.target_for(
        IntensityReference.VMA_PERCENT
    )

    assert vma is not None

    assert vma.minimum == 80
    assert vma.maximum == 90


def test_orchestrator_loads_profile_once() -> None:
    service, profile_repository = (
        create_service()
    )

    service.generate(
        athlete_profile_id=uuid4(),
        envelope=create_envelope(),
        reference_date=REFERENCE_DATE,
    )

    assert (
        profile_repository.get_calls
        == 1
    )


def test_reference_date_defaults_to_week_start() -> None:
    service, _ = create_service()

    week = service.generate(
        athlete_profile_id=uuid4(),
        envelope=create_envelope(),
    )

    assert week.session_count == 1


def test_missing_measurements_do_not_block_generation() -> None:
    service, _ = create_service(
        measurements=()
    )

    week = service.generate(
        athlete_profile_id=uuid4(),
        envelope=create_envelope(),
        reference_date=REFERENCE_DATE,
    )

    prescription = (
        week.sessions[0]
        .proposal
        .intensity_prescription
    )

    assert prescription is not None

    # Selon les données par défaut du profil, OpenCoach peut
    # utiliser une valeur legacy. Si aucune cible physiologique
    # exploitable n'existe, le RPE reste toujours disponible.
    rpe = prescription.target_for(
        IntensityReference.RPE
    )

    assert rpe is not None

    assert rpe.minimum == 7
    assert rpe.maximum == 8
