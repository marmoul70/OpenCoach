"""Tests d'intégration de la génération physiologique hebdomadaire."""

from datetime import date

from opencoach.planning.sessions.coach_port import (
    SessionCoachRequest,
)

from opencoach.coaching.generation import (
    WeeklyTrainingGenerationService,
)
from opencoach.planning.physiology.snapshot import (
    PhysiologicalCalibrationMetric,
    PhysiologicalCalibrationSnapshot,
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


def create_metric(
    *,
    metric,
    value,
    usable=True,
) -> PhysiologicalCalibrationMetric:
    """Construit une métrique physiologique pour les tests."""

    return PhysiologicalCalibrationMetric(
        metric=metric,
        value=value,
        source=(
            "history"
            if value is not None
            else "missing"
        ),
        measurement=None,
        freshness=None,
        usable=usable,
        recalibration_recommended=(
            not usable
        ),
        reason="Métrique de test.",
    )


def create_physiology() -> PhysiologicalCalibrationSnapshot:
    """Construit un profil physiologique complet et utilisable."""

    return PhysiologicalCalibrationSnapshot(
        vma=create_metric(
            metric="vma",
            value=15.0,
        ),
        max_heart_rate=create_metric(
            metric="max_heart_rate",
            value=181.0,
        ),
        resting_heart_rate=create_metric(
            metric="resting_heart_rate",
            value=50.0,
        ),
        threshold_heart_rate_1=create_metric(
            metric="threshold_heart_rate_1",
            value=145.0,
        ),
        threshold_heart_rate_2=create_metric(
            metric="threshold_heart_rate_2",
            value=165.0,
        ),
    )


def create_speed_slot() -> WeeklySessionIntentSlot:
    """Construit une séance de développement de vitesse."""

    intent = SessionIntent(
        primary_stimulus=(
            TrainingStimulus.SPEED_DEVELOPMENT
        ),
        secondary_stimuli=(),
        importance=SessionIntentImportance.KEY,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.FORBIDDEN,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        required_modalities=(
            TrainingModality.RUNNING,
        ),
        duration_min_minutes=30,
        duration_max_minutes=60,
    )

    return WeeklySessionIntentSlot(
        slot_id="speed",
        day=Weekday.MONDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.HIGH,
        duration_available_minutes=60,
        preserve_next_key_session=False,
        preferred_recovery_before_hours=36,
        preferred_recovery_after_hours=36,
    )


def create_threshold_slot() -> WeeklySessionIntentSlot:
    """Construit une séance seuil de 70 minutes."""

    intent = SessionIntent(
        primary_stimulus=TrainingStimulus.THRESHOLD,
        secondary_stimuli=(),
        importance=SessionIntentImportance.IMPORTANT,
        specificity=SpecificityLevel.HIGH,
        substitution=SubstitutionPolicy.ALLOWED,
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


def create_easy_slot() -> WeeklySessionIntentSlot:
    """Construit une séance d'endurance facile."""

    intent = SessionIntent(
        primary_stimulus=(
            TrainingStimulus.AEROBIC_EASY
        ),
        secondary_stimuli=(),
        importance=SessionIntentImportance.SUPPORT,
        specificity=SpecificityLevel.LOW,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        required_modalities=(),
        duration_min_minutes=45,
        duration_max_minutes=45,
    )

    return WeeklySessionIntentSlot(
        slot_id="easy-monday",
        day=Weekday.MONDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.LOW,
        duration_available_minutes=45,
    )


def create_envelope(
    *slots: WeeklySessionIntentSlot,
) -> WeeklyTrainingEnvelope:
    """Construit l'enveloppe hebdomadaire de test."""

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
        session_slots=slots,
        schedule_pressure=(
            SchedulePressure.MODERATE
        ),
    )


def test_threshold_week_uses_real_physiology() -> None:
    """Le seuil réel de l'athlète doit devenir la cible principale."""

    service = WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )

    week = service.generate(
        envelope=create_envelope(
            create_threshold_slot()
        ),
        physiology=create_physiology(),
    )

    assert week.session_count == 1

    session = week.sessions[0]

    prescription = (
        session.proposal.intensity_prescription
    )

    assert prescription is not None

    assert (
        prescription.stimulus
        is TrainingStimulus.THRESHOLD
    )

    assert (
        prescription.primary_target.reference
        is IntensityReference.HEART_RATE
    )

    # SV2 = 165 bpm.
    # La politique seuil utilise 95 à 100 % du SV2.
    assert (
        prescription.primary_target.minimum
        == 157
    )

    assert (
        prescription.primary_target.maximum
        == 165
    )


def test_threshold_week_exposes_vma_and_rpe_fallbacks() -> None:
    """Le seuil doit aussi conserver VMA et RPE comme références."""

    service = WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )

    week = service.generate(
        envelope=create_envelope(
            create_threshold_slot()
        ),
        physiology=create_physiology(),
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

    rpe = prescription.target_for(
        IntensityReference.RPE
    )

    assert vma is not None

    assert vma.minimum == 80
    assert vma.maximum == 90

    assert rpe is not None

    assert rpe.minimum == 7
    assert rpe.maximum == 8


def test_threshold_week_contains_interval_structure() -> None:
    """La physiologie et la structure doivent coexister."""

    service = WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )

    week = service.generate(
        envelope=create_envelope(
            create_threshold_slot()
        ),
        physiology=create_physiology(),
    )

    structure = (
        week.sessions[0]
        .proposal
        .work_structure
    )

    assert structure is not None

    assert (
        structure.structure_type
        is WorkStructureType.INTERVALS
    )

    assert structure.intervals


def test_easy_session_uses_heart_rate_reserve() -> None:
    """L'endurance facile doit utiliser la réserve cardiaque."""

    service = WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )

    week = service.generate(
        envelope=create_envelope(
            create_easy_slot()
        ),
        physiology=create_physiology(),
    )

    prescription = (
        week.sessions[0]
        .proposal
        .intensity_prescription
    )

    assert prescription is not None

    target = prescription.target_for(
        IntensityReference.HEART_RATE_RESERVE
    )

    assert target is not None

    # Réserve cardiaque :
    # 181 - 50 = 131 bpm.
    #
    # Minimum :
    # 50 + 131 × 55 % = 122.05 -> 122.
    #
    # Maximum :
    # 50 + 131 × 70 % = 141.7 -> 142.
    assert target.minimum == 122
    assert target.maximum == 142


def test_easy_session_exposes_vma_reference() -> None:
    """L'endurance facile doit également exposer la plage VMA."""

    service = WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )

    week = service.generate(
        envelope=create_envelope(
            create_easy_slot()
        ),
        physiology=create_physiology(),
    )

    prescription = (
        week.sessions[0]
        .proposal
        .intensity_prescription
    )

    assert prescription is not None

    target = prescription.target_for(
        IntensityReference.VMA_PERCENT
    )

    assert target is not None

    assert target.minimum == 60
    assert target.maximum == 70


def test_generation_without_physiology_falls_back_to_rpe() -> None:
    """L'absence de calibration ne doit jamais bloquer la semaine."""

    service = WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )

    week = service.generate(
        envelope=create_envelope(
            create_threshold_slot()
        ),
        physiology=None,
    )

    prescription = (
        week.sessions[0]
        .proposal
        .intensity_prescription
    )

    assert prescription is not None

    assert (
        prescription.primary_target.reference
        is IntensityReference.RPE
    )

    assert (
        prescription.primary_target.minimum
        == 7
    )

    assert (
        prescription.primary_target.maximum
        == 8
    )


def test_complete_week_uses_same_physiology_for_each_session() -> None:
    """Une même calibration doit alimenter toute la semaine."""

    service = WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )

    week = service.generate(
        envelope=create_envelope(
            create_easy_slot(),
            create_threshold_slot(),
        ),
        physiology=create_physiology(),
    )

    assert week.session_count == 2

    easy = week.session_for_day(
        Weekday.MONDAY
    )

    threshold = week.session_for_day(
        Weekday.WEDNESDAY
    )

    assert easy is not None
    assert threshold is not None

    easy_prescription = (
        easy.proposal.intensity_prescription
    )

    threshold_prescription = (
        threshold.proposal.intensity_prescription
    )

    assert easy_prescription is not None
    assert threshold_prescription is not None

    assert (
        easy_prescription.target_for(
            IntensityReference.HEART_RATE_RESERVE
        )
        is not None
    )

    assert (
        threshold_prescription.primary_target.reference
        is IntensityReference.HEART_RATE
    )


def test_speed_development_distance_interval_uses_vma_for_repetition_target() -> None:
    slot = create_speed_slot()

    generator = DeterministicSessionGenerator()

    proposal = generator.generate_session(
        request=SessionCoachRequest(
            phase=TrainingPhase.BASE,
            slot=slot,
            planned_duration_minutes=45,
            phase_week_index=2,
            physiology=create_physiology(),
        )
    )

    assert proposal.work_structure is not None

    interval = proposal.work_structure.intervals[0]

    assert interval.work_distance_meters == 200

    assert interval.repetition_target is not None

    assert (
        interval.repetition_target.rounded_fast_seconds
        == 42
    )

    assert (
        interval.repetition_target.rounded_slow_seconds
        == 48
    )


def test_speed_development_without_usable_vma_has_no_repetition_target() -> None:
    physiology = create_physiology()

    unavailable_vma = create_metric(
        metric="vma",
        value=15.0,
        usable=False,
    )

    physiology = PhysiologicalCalibrationSnapshot(
        vma=unavailable_vma,
        max_heart_rate=physiology.max_heart_rate,
        resting_heart_rate=physiology.resting_heart_rate,
        threshold_heart_rate_1=(
            physiology.threshold_heart_rate_1
        ),
        threshold_heart_rate_2=(
            physiology.threshold_heart_rate_2
        ),
    )

    generator = DeterministicSessionGenerator()

    proposal = generator.generate_session(
        request=SessionCoachRequest(
            phase=TrainingPhase.BASE,
            slot=create_speed_slot(),
            planned_duration_minutes=45,
            phase_week_index=2,
            physiology=physiology,
        )
    )

    assert proposal.work_structure is not None

    interval = proposal.work_structure.intervals[0]

    assert interval.work_distance_meters == 200

    assert interval.repetition_target is None
