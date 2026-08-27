from dataclasses import replace

from datetime import date

import pytest

from opencoach.coaching.generation import (
    WeeklyTrainingGenerationError,
    WeeklyTrainingGenerationService,
)
from opencoach.planning.sessions.fake_coach import (
    FakeSessionCoach,
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
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
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
from opencoach.planning.sessions.generators import (
    DeterministicSessionGenerator,
)
from opencoach.planning.sessions.prescription import (
    WorkStructureType,
)


def create_slot(
    *,
    slot_id: str,
    day: Weekday,
    stimulus: TrainingStimulus,
    duration: int = 60,
) -> WeeklySessionIntentSlot:
    intent = SessionIntent(
        primary_stimulus=stimulus,
        secondary_stimuli=(),
        importance=(
            SessionIntentImportance.IMPORTANT
        ),
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        required_modalities=(),
        duration_min_minutes=duration,
        duration_max_minutes=duration,
    )

    return WeeklySessionIntentSlot(
        slot_id=slot_id,
        day=day,
        intent=intent,
        fatigue_budget=FatigueBudget.MODERATE,
        duration_available_minutes=duration,
    )


def create_envelope(
    *,
    slots,
) -> WeeklyTrainingEnvelope:
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
        week_type=TrajectoryWeekType.LOADING,
        target_load=420.0,
        load_min=380.0,
        load_max=460.0,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SUNDAY,
        ),
        session_slots=tuple(
            slots
        ),
        schedule_pressure=(
            SchedulePressure.MODERATE
        ),
        notes=(
            "Semaine spécifique.",
        ),
    )


def test_generates_complete_week() -> None:
    envelope = create_envelope(
        slots=(
            create_slot(
                slot_id="monday",
                day=Weekday.MONDAY,
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
                duration=45,
            ),
            create_slot(
                slot_id="wednesday",
                day=Weekday.WEDNESDAY,
                stimulus=(
                    TrainingStimulus.THRESHOLD
                ),
                duration=60,
            ),
            create_slot(
                slot_id="sunday",
                day=Weekday.SUNDAY,
                stimulus=(
                    TrainingStimulus.LONG_ENDURANCE
                ),
                duration=120,
            ),
        )
    )

    service = (
        WeeklyTrainingGenerationService(
            session_generator=(
                FakeSessionCoach()
            )
        )
    )

    week = service.generate(
        envelope=envelope
    )

    assert week.session_count == 3

    assert (
        week.total_duration_minutes
        == 225
    )

    assert (
        week.sessions[0].date
        == date(
            2027,
            7,
            5,
        )
    )

    assert (
        week.sessions[1].date
        == date(
            2027,
            7,
            7,
        )
    )

    assert (
        week.sessions[2].date
        == date(
            2027,
            7,
            11,
        )
    )


def test_sessions_are_sorted_chronologically() -> None:
    envelope = create_envelope(
        slots=(
            create_slot(
                slot_id="sunday",
                day=Weekday.SUNDAY,
                stimulus=(
                    TrainingStimulus.LONG_ENDURANCE
                ),
            ),
            create_slot(
                slot_id="monday",
                day=Weekday.MONDAY,
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
            ),
        )
    )

    service = (
        WeeklyTrainingGenerationService(
            session_generator=(
                FakeSessionCoach()
            )
        )
    )

    week = service.generate(
        envelope=envelope
    )

    assert (
        tuple(
            session.day
            for session in week.sessions
        )
        == (
            Weekday.MONDAY,
            Weekday.SUNDAY,
        )
    )


def test_week_exposes_session_by_day() -> None:
    envelope = create_envelope(
        slots=(
            create_slot(
                slot_id="monday",
                day=Weekday.MONDAY,
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
            ),
        )
    )

    service = (
        WeeklyTrainingGenerationService(
            session_generator=(
                FakeSessionCoach()
            )
        )
    )

    week = service.generate(
        envelope=envelope
    )

    session = week.session_for_day(
        Weekday.MONDAY
    )

    assert session is not None

    assert (
        session.slot_id
        == "monday"
    )

    assert (
        week.session_for_day(
            Weekday.SUNDAY
        )
        is None
    )


def test_empty_envelope_generates_empty_week() -> None:
    envelope = create_envelope(
        slots=()
    )

    service = (
        WeeklyTrainingGenerationService(
            session_generator=(
                FakeSessionCoach()
            )
        )
    )

    week = service.generate(
        envelope=envelope
    )

    assert week.session_count == 0

    assert (
        week.total_duration_minutes
        == 0
    )


def test_day_outside_envelope_is_rejected() -> None:
    envelope = WeeklyTrainingEnvelope(
        week_start=date(
            2027,
            7,
            5,
        ),
        week_end=date(
            2027,
            7,
            9,
        ),
        phase=TrainingPhase.BASE,
        week_type=TrajectoryWeekType.LOADING,
        target_load=None,
        load_min=None,
        load_max=None,
        available_days=(
            Weekday.SUNDAY,
        ),
        session_slots=(
            create_slot(
                slot_id="sunday",
                day=Weekday.SUNDAY,
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
            ),
        ),
        schedule_pressure=(
            SchedulePressure.LOW
        ),
    )

    service = (
        WeeklyTrainingGenerationService(
            session_generator=(
                FakeSessionCoach()
            )
        )
    )

    with pytest.raises(
        WeeklyTrainingGenerationError,
        match="aucune date",
    ):
        service.generate(
            envelope=envelope
        )


def test_generated_week_preserves_envelope_metadata() -> None:
    envelope = create_envelope(
        slots=()
    )

    service = (
        WeeklyTrainingGenerationService(
            session_generator=(
                FakeSessionCoach()
            )
        )
    )

    week = service.generate(
        envelope=envelope
    )

    assert (
        week.phase
        is TrainingPhase.SPECIFIC
    )

    assert week.target_load == 420.0

    assert (
        week.notes
        == (
            "Semaine spécifique.",
        )
    )

def test_week_generation_uses_real_deterministic_generator() -> None:
    envelope = create_envelope(
        slots=(
            create_slot(
                slot_id="threshold",
                day=Weekday.WEDNESDAY,
                stimulus=(
                    TrainingStimulus.THRESHOLD
                ),
                duration=70,
            ),
        )
    )

    service = (
        WeeklyTrainingGenerationService(
            session_generator=(
                DeterministicSessionGenerator()
            )
        )
    )

    week = service.generate(
        envelope=envelope
    )

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

    assert (
        session.proposal.intensity_prescription
        is not None
    )

def test_generation_uses_long_endurance_reference() -> None:
    """La génération respecte la baseline de sortie longue."""

    long_slot = create_slot(
        slot_id="session-1-long_endurance",
        day=Weekday.MONDAY,
        stimulus=TrainingStimulus.LONG_ENDURANCE,
    )

    easy_one = create_slot(
        slot_id="session-2-easy",
        day=Weekday.WEDNESDAY,
        stimulus=TrainingStimulus.AEROBIC_EASY,
    )

    easy_two = create_slot(
        slot_id="session-3-easy",
        day=Weekday.FRIDAY,
        stimulus=TrainingStimulus.AEROBIC_EASY,
    )

    quality = create_slot(
        slot_id="session-4-threshold",
        day=Weekday.SUNDAY,
        stimulus=TrainingStimulus.THRESHOLD,
    )

    long_slot = replace(
        long_slot,
        intent=replace(
            long_slot.intent,
            duration_min_minutes=60,
            duration_max_minutes=300,
        ),
        duration_available_minutes=None,
    )

    easy_one = replace(
        easy_one,
        intent=replace(
            easy_one.intent,
            duration_min_minutes=30,
            duration_max_minutes=120,
        ),
        duration_available_minutes=None,
    )

    easy_two = replace(
        easy_two,
        intent=replace(
            easy_two.intent,
            duration_min_minutes=30,
            duration_max_minutes=120,
        ),
        duration_available_minutes=None,
    )

    quality = replace(
        quality,
        intent=replace(
            quality.intent,
            duration_min_minutes=30,
            duration_max_minutes=120,
        ),
        duration_available_minutes=None,
    )

    envelope = replace(
        create_envelope(
            slots=(
                long_slot,
                easy_one,
                easy_two,
                quality,
            ),
        ),
        target_duration_minutes=255.0,
        long_endurance_reference_minutes=173.0,
    )

    service = WeeklyTrainingGenerationService(
        session_generator=DeterministicSessionGenerator()
    )

    result = service.generate(
        envelope=envelope,
    )

    durations = {
        session.slot_id:
            session.proposal.duration_minutes
        for session in result.sessions
    }

    assert (
        durations["session-1-long_endurance"]
        == 165
    )

    assert durations["session-2-easy"] == 30
    assert durations["session-3-easy"] == 30
    assert durations["session-4-threshold"] == 30

    assert sum(
        durations.values()
    ) == 255




def test_generated_week_exposes_multiple_sessions_for_same_day() -> None:
    envelope = create_envelope(
        slots=(
            create_slot(
                slot_id="monday-easy",
                day=Weekday.MONDAY,
                stimulus=TrainingStimulus.AEROBIC_EASY,
                duration=45,
            ),
            create_slot(
                slot_id="monday-strength",
                day=Weekday.MONDAY,
                stimulus=TrainingStimulus.STRENGTH_LOWER_BODY,
                duration=20,
            ),
        )
    )

    service = WeeklyTrainingGenerationService(
        session_generator=FakeSessionCoach()
    )

    week = service.generate(
        envelope=envelope
    )

    sessions = week.sessions_for_day(
        Weekday.MONDAY
    )

    assert week.session_count == 2

    assert len(sessions) == 2

    assert tuple(
        session.slot_id
        for session in sessions
    ) == (
        "monday-easy",
        "monday-strength",
    )


def test_generation_uses_target_weekly_duration_not_reference_duration() -> None:
    """La génération consomme le budget cible et non la référence historique."""

    def flexible_slot(
        *,
        slot_id: str,
        day: Weekday,
        stimulus: TrainingStimulus,
        minimum: int,
        maximum: int,
        importance: SessionIntentImportance,
    ) -> WeeklySessionIntentSlot:
        intent = SessionIntent(
            primary_stimulus=stimulus,
            secondary_stimuli=(),
            importance=importance,
            specificity=SpecificityLevel.MODERATE,
            substitution=SubstitutionPolicy.ALLOWED,
            preferred_modalities=(
                TrainingModality.RUNNING,
            ),
            required_modalities=(),
            duration_min_minutes=minimum,
            duration_max_minutes=maximum,
        )

        return WeeklySessionIntentSlot(
            slot_id=slot_id,
            day=day,
            intent=intent,
            fatigue_budget=FatigueBudget.MODERATE,
            duration_available_minutes=maximum,
        )

    envelope = create_envelope(
        slots=(
            flexible_slot(
                slot_id="quality",
                day=Weekday.MONDAY,
                stimulus=TrainingStimulus.THRESHOLD,
                minimum=45,
                maximum=90,
                importance=(
                    SessionIntentImportance.IMPORTANT
                ),
            ),
            flexible_slot(
                slot_id="easy-1",
                day=Weekday.WEDNESDAY,
                stimulus=TrainingStimulus.AEROBIC_EASY,
                minimum=45,
                maximum=120,
                importance=(
                    SessionIntentImportance.SUPPORT
                ),
            ),
            flexible_slot(
                slot_id="easy-2",
                day=Weekday.FRIDAY,
                stimulus=TrainingStimulus.AEROBIC_EASY,
                minimum=45,
                maximum=120,
                importance=(
                    SessionIntentImportance.SUPPORT
                ),
            ),
            flexible_slot(
                slot_id="long",
                day=Weekday.SUNDAY,
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                minimum=60,
                maximum=240,
                importance=(
                    SessionIntentImportance.KEY
                ),
            ),
        )
    )

    envelope = replace(
        envelope,
        reference_duration_minutes=300.0,
        target_duration_minutes=330.0,
        long_endurance_reference_minutes=150.0,
    )

    service = WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )

    week = service.generate(
        envelope=envelope
    )

    assert (
        week.total_duration_minutes
        == 330
    )

    assert sum(
        session.proposal.duration_minutes
        for session in week.sessions
    ) == 330
