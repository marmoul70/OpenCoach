"""Tests du service applicatif de génération et persistance."""

from datetime import date
from uuid import uuid4

from opencoach.coaching.generation import (
    GenerateAndPersistTrainingWeekService,
)
from opencoach.coaching.generation.models import (
    GeneratedTrainingWeek,
)
from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


class FakeGenerationService:
    """Double minimal du générateur hebdomadaire."""

    def __init__(
        self,
        week: GeneratedTrainingWeek,
    ) -> None:
        self.week = week

        self.calls = []

    def generate(
        self,
        *,
        athlete_profile_id,
        envelope,
        reference_date=None,
        additional_context=(),
    ):
        self.calls.append(
            {
                "athlete_profile_id":
                    athlete_profile_id,
                "envelope":
                    envelope,
                "reference_date":
                    reference_date,
                "additional_context":
                    additional_context,
            }
        )

        return self.week


class FakePersistenceService:
    """Double minimal du service de persistance."""

    def __init__(
        self,
        sessions=(),
    ) -> None:
        self.sessions = tuple(
            sessions
        )

        self.calls = []

    def persist(
        self,
        *,
        athlete_profile_id,
        week,
    ):
        self.calls.append(
            {
                "athlete_profile_id":
                    athlete_profile_id,
                "week":
                    week,
            }
        )

        return self.sessions


class FakeEnvelope:
    """Objet sentinelle suffisant pour ce test applicatif."""


def create_generated_week() -> GeneratedTrainingWeek:
    return GeneratedTrainingWeek(
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
        sessions=(),
        target_load=420.0,
    )


def create_training_session() -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=date(
            2027,
            7,
            7,
        ),
        type="threshold",
        sport_type="Run",
        title="Travail au seuil",
        description="Séance test.",
        duration_minutes=70,
        planning_key=(
            "2027-07-05:threshold"
        ),
    )


def test_execute_generates_then_persists_week() -> None:
    generated_week = (
        create_generated_week()
    )

    persisted_session = (
        create_training_session()
    )

    generation_service = (
        FakeGenerationService(
            generated_week
        )
    )

    persistence_service = (
        FakePersistenceService(
            (
                persisted_session,
            )
        )
    )

    service = (
        GenerateAndPersistTrainingWeekService(
            generation_service=(
                generation_service
            ),
            persistence_service=(
                persistence_service
            ),
        )
    )

    athlete_profile_id = uuid4()

    envelope = FakeEnvelope()

    result = service.execute(
        athlete_profile_id=(
            athlete_profile_id
        ),
        envelope=envelope,
        reference_date=date(
            2027,
            7,
            5,
        ),
        additional_context=(
            "Semaine de test.",
        ),
    )

    assert (
        result.generated_week
        is generated_week
    )

    assert (
        result.persisted_sessions
        == (
            persisted_session,
        )
    )

    assert result.session_count == 1


def test_execute_passes_context_to_generation_service() -> None:
    generated_week = (
        create_generated_week()
    )

    generation_service = (
        FakeGenerationService(
            generated_week
        )
    )

    persistence_service = (
        FakePersistenceService()
    )

    service = (
        GenerateAndPersistTrainingWeekService(
            generation_service=(
                generation_service
            ),
            persistence_service=(
                persistence_service
            ),
        )
    )

    athlete_profile_id = uuid4()

    envelope = FakeEnvelope()

    reference_date = date(
        2027,
        7,
        5,
    )

    service.execute(
        athlete_profile_id=(
            athlete_profile_id
        ),
        envelope=envelope,
        reference_date=(
            reference_date
        ),
        additional_context=(
            "Fatigue légère.",
        ),
    )

    assert len(
        generation_service.calls
    ) == 1

    call = (
        generation_service.calls[
            0
        ]
    )

    assert (
        call["athlete_profile_id"]
        == athlete_profile_id
    )

    assert (
        call["envelope"]
        is envelope
    )

    assert (
        call["reference_date"]
        == reference_date
    )

    assert (
        call["additional_context"]
        == (
            "Fatigue légère.",
        )
    )


def test_execute_persists_generated_week() -> None:
    generated_week = (
        create_generated_week()
    )

    generation_service = (
        FakeGenerationService(
            generated_week
        )
    )

    persistence_service = (
        FakePersistenceService()
    )

    service = (
        GenerateAndPersistTrainingWeekService(
            generation_service=(
                generation_service
            ),
            persistence_service=(
                persistence_service
            ),
        )
    )

    athlete_profile_id = uuid4()

    service.execute(
        athlete_profile_id=(
            athlete_profile_id
        ),
        envelope=FakeEnvelope(),
    )

    assert len(
        persistence_service.calls
    ) == 1

    call = (
        persistence_service.calls[
            0
        ]
    )

    assert (
        call["athlete_profile_id"]
        == athlete_profile_id
    )

    assert (
        call["week"]
        is generated_week
    )


def test_execute_with_empty_week_is_valid() -> None:
    generated_week = (
        create_generated_week()
    )

    service = (
        GenerateAndPersistTrainingWeekService(
            generation_service=(
                FakeGenerationService(
                    generated_week
                )
            ),
            persistence_service=(
                FakePersistenceService()
            ),
        )
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        envelope=FakeEnvelope(),
    )

    assert result.session_count == 0
