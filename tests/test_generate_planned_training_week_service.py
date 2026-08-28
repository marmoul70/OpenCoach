"""Tests du pipeline complet de planning hebdomadaire."""

from datetime import date
from uuid import uuid4

from opencoach.coaching.generation import (
    GeneratePlannedTrainingWeekService,
)
from opencoach.coaching.generation.application import (
    GenerateAndPersistTrainingWeekResult,
)
from opencoach.coaching.generation.models import (
    GeneratedTrainingWeek,
)
from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
    WeeklyTrainingAverages,
)
from opencoach.planning.trajectory.service import (
    CurrentWeekCoachingInput,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)

from opencoach.physiology.testing.models import (
    SportDiscipline,
)


class FakeGenerateAndPersistService:
    """Double de la génération concrète."""

    def __init__(
        self,
    ) -> None:
        self.calls = []

    def execute(
        self,
        *,
        athlete_profile_id,
        envelope,
        reference_date=None,
        reconcile_from_date=None,
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
                "reconcile_from_date":
                    reconcile_from_date,
                "additional_context":
                    additional_context,
            }
        )

        week = GeneratedTrainingWeek(
            week_start=(
                envelope.week_start
            ),
            week_end=(
                envelope.week_end
            ),
            phase=envelope.phase,
            sessions=(),
            target_load=(
                envelope.target_load
            ),
            notes=envelope.notes,
        )

        return (
            GenerateAndPersistTrainingWeekResult(
                generated_week=week,
                persisted_sessions=(),
            )
        )


class FakePhysiologicalTestService:
    """Espion du raccord automatique des tests physiologiques."""

    def __init__(
        self,
    ) -> None:
        self.calls = []

    def evaluate_week(
        self,
        request,
    ):
        self.calls.append(
            request
        )

        return None


def create_average(
    *,
    training_load: float,
) -> WeeklyTrainingAverages:
    return WeeklyTrainingAverages(
        weeks=1.0,
        sessions=4.0,
        duration_minutes=300.0,
        distance_km=40.0,
        elevation_gain_m=1000.0,
        training_load=training_load,
    )


def create_history_metrics() -> TrainingHistoryMetrics:
    """Historique cohérent pour construire une trajectoire."""

    return TrainingHistoryMetrics(
        last_7_days=create_average(
            training_load=310.0,
        ),
        last_28_days=create_average(
            training_load=300.0,
        ),
        last_42_days=create_average(
            training_load=300.0,
        ),
        last_84_days=create_average(
            training_load=295.0,
        ),
        longest_activity=None,
        longest_duration_minutes=None,
        longest_distance_km=None,
        highest_elevation_activity=None,
        highest_elevation_gain_m=None,
    )


def create_planning_input() -> CurrentWeekCoachingInput:
    return CurrentWeekCoachingInput(
        trajectory_start_date=date(
            2027,
            6,
            7,
        ),
        planning_date=date(
            2027,
            7,
            5,
        ),
        target_race_date=date(
            2027,
            9,
            18,
        ),
        target_distance_km=65.0,
        target_elevation_gain_m=3000.0,
        trajectory_history_metrics=(
            create_history_metrics()
        ),
        history_metrics=(
            create_history_metrics()
        ),
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SUNDAY,
        ),
    )


def test_service_builds_planning_before_generation() -> None:
    generator = (
        FakeGenerateAndPersistService()
    )

    service = (
        GeneratePlannedTrainingWeekService(
            generation_service=generator
        )
    )

    athlete_profile_id = uuid4()

    result = service.execute(
        athlete_profile_id=(
            athlete_profile_id
        ),
        planning_input=(
            create_planning_input()
        ),
    )

    assert result.planning is not None

    assert (
        result.planning.coaching.envelope
        is generator.calls[0]["envelope"]
    )


def test_service_passes_correct_athlete_to_generation() -> None:
    generator = (
        FakeGenerateAndPersistService()
    )

    service = (
        GeneratePlannedTrainingWeekService(
            generation_service=generator
        )
    )

    athlete_profile_id = uuid4()

    service.execute(
        athlete_profile_id=(
            athlete_profile_id
        ),
        planning_input=(
            create_planning_input()
        ),
    )

    assert (
        generator.calls[0][
            "athlete_profile_id"
        ]
        == athlete_profile_id
    )


def test_service_passes_physiological_reference_date() -> None:
    generator = (
        FakeGenerateAndPersistService()
    )

    service = (
        GeneratePlannedTrainingWeekService(
            generation_service=generator
        )
    )

    reference_date = date(
        2027,
        7,
        4,
    )

    service.execute(
        athlete_profile_id=uuid4(),
        planning_input=(
            create_planning_input()
        ),
        physiological_reference_date=(
            reference_date
        ),
    )

    assert (
        generator.calls[0][
            "reference_date"
        ]
        == reference_date
    )


def test_service_passes_additional_context() -> None:
    generator = (
        FakeGenerateAndPersistService()
    )

    service = (
        GeneratePlannedTrainingWeekService(
            generation_service=generator
        )
    )

    service.execute(
        athlete_profile_id=uuid4(),
        planning_input=(
            create_planning_input()
        ),
        additional_context=(
            "Semaine avec disponibilité réduite.",
        ),
    )

    assert (
        generator.calls[0][
            "additional_context"
        ]
        == (
            "Semaine avec disponibilité réduite.",
        )
    )


def test_result_exposes_session_count() -> None:
    service = (
        GeneratePlannedTrainingWeekService(
            generation_service=(
                FakeGenerateAndPersistService()
            )
        )
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        planning_input=(
            create_planning_input()
        ),
    )

    assert result.session_count == 0


def test_service_evaluates_physiological_test_after_generation() -> None:
    """Le planning transmet le contexte au moteur automatique de tests."""

    generator = (
        FakeGenerateAndPersistService()
    )

    physiological_service = (
        FakePhysiologicalTestService()
    )

    service = (
        GeneratePlannedTrainingWeekService(
            generation_service=(
                generator
            ),
            physiological_test_service=(
                physiological_service
            ),
        )
    )

    athlete_profile_id = uuid4()

    reference_date = date(
        2027,
        7,
        5,
    )

    disciplines = (
        SportDiscipline.ROAD_RUNNING,
        SportDiscipline.TRAIL_RUNNING,
    )

    result = service.execute(
        athlete_profile_id=(
            athlete_profile_id
        ),
        planning_input=(
            create_planning_input()
        ),
        physiological_reference_date=(
            reference_date
        ),
        sport_disciplines=(
            disciplines
        ),
    )

    assert len(
        physiological_service.calls
    ) == 1

    request = (
        physiological_service.calls[
            0
        ]
    )

    assert (
        request.athlete_profile_id
        == athlete_profile_id
    )

    assert (
        request.reference_date
        == reference_date
    )

    assert (
        request.week_start
        == result.generation.generated_week.week_start
    )

    assert (
        request.week_end
        == result.generation.generated_week.week_end
    )

    assert (
        request.phase
        == result.generation.generated_week.phase
    )

    assert (
        request.disciplines
        == disciplines
    )


def test_service_does_not_evaluate_test_without_sport_disciplines() -> None:
    """Aucune proposition automatique sans préférence sportive."""

    physiological_service = (
        FakePhysiologicalTestService()
    )

    service = (
        GeneratePlannedTrainingWeekService(
            generation_service=(
                FakeGenerateAndPersistService()
            ),
            physiological_test_service=(
                physiological_service
            ),
        )
    )

    service.execute(
        athlete_profile_id=uuid4(),
        planning_input=(
            create_planning_input()
        ),
    )

    assert (
        physiological_service.calls
        == []
    )
