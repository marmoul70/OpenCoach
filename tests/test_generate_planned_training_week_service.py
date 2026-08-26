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
