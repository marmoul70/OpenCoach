"""Tests de préparation du contexte hebdomadaire OpenCoach."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from opencoach.coaching.generation.context import (
    WeeklyPlanningContextBuilder,
    WeeklyPlanningContextError,
)
from opencoach.models import (
    AthleteProfile,
    AthleteTraining,
    Race,
)
from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
    WeeklyTrainingAverages,
)
from opencoach.planning.trajectory.coaching import (
    TrainingPhase,
)
from opencoach.planning.trajectory.service import (
    build_current_week_coaching,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)


PLANNING_DATE = date(
    2027,
    7,
    5,
)

TRAJECTORY_START_DATE = date(
    2027,
    6,
    7,
)


class FakePlanningContextService:
    """Double du service de contexte consolidé."""

    def __init__(
        self,
        context,
    ) -> None:
        self.context = context
        self.calls = []

    def build(
        self,
        athlete_profile_id,
        planning_date,
    ):
        self.calls.append(
            {
                "athlete_profile_id":
                    athlete_profile_id,
                "planning_date":
                    planning_date,
            }
        )

        return self.context


class FakeHistoryService:
    """Double du service d'historique."""

    def __init__(
        self,
        snapshot=None,
    ) -> None:
        self.snapshot = (
            snapshot
            if snapshot is not None
            else object()
        )

        self.calls = []

    def build(
        self,
        athlete_profile_id,
        reference_date,
    ):
        self.calls.append(
            {
                "athlete_profile_id":
                    athlete_profile_id,
                "reference_date":
                    reference_date,
            }
        )

        return self.snapshot


def create_race(
    *,
    race_date=None,
    distance_km=65.0,
    elevation_gain_m=3000.0,
):
    if race_date is None:
        race_date = date(
            2027,
            9,
            18,
        )

    return Race(
        id=uuid4(),
        date=race_date,
        name="Ultra test",
        location="Jura",
        race_type="trail",
        priority="primary",
        distance_km=distance_km,
        elevation_gain_m=(
            elevation_gain_m
        ),
        status="planned",
    )


def create_athlete(
    *,
    available_days=None,
    weekly_sessions=4,
):
    if available_days is None:
        available_days = [
            0,
            2,
            4,
            6,
        ]

    return AthleteProfile(
        training=AthleteTraining(
            weekly_sessions=(
                weekly_sessions
            ),
            available_days=(
                available_days
            ),
        )
    )


def create_context(
    *,
    athlete=None,
    primary_race=None,
    training_races=(),
    readiness=None,
    constraints=(),
):
    if athlete is None:
        athlete = create_athlete()

    if primary_race is None:
        primary_race = create_race()

    return SimpleNamespace(
        athlete=athlete,
        primary_race=primary_race,
        training_races=tuple(
            training_races
        ),
        readiness=readiness,
        constraints=tuple(
            constraints
        ),
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


def create_metrics() -> TrainingHistoryMetrics:
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


def create_builder(
    *,
    context=None,
):
    if context is None:
        context = create_context()

    planning_service = (
        FakePlanningContextService(
            context
        )
    )

    history_service = (
        FakeHistoryService()
    )

    builder = WeeklyPlanningContextBuilder(
        planning_context_service=(
            planning_service
        ),
        history_service=(
            history_service
        ),
    )

    return (
        builder,
        planning_service,
        history_service,
    )


def test_available_days_are_converted_to_weekdays() -> None:
    values = (
        WeeklyPlanningContextBuilder
        ._available_days(
            [
                0,
                2,
                4,
                6,
            ]
        )
    )

    assert values == (
        Weekday.MONDAY,
        Weekday.WEDNESDAY,
        Weekday.FRIDAY,
        Weekday.SUNDAY,
    )


def test_invalid_available_day_is_rejected() -> None:
    with pytest.raises(
        WeeklyPlanningContextError,
        match="jour",
    ):
        (
            WeeklyPlanningContextBuilder
            ._available_days(
                [
                    7,
                ]
            )
        )


def test_missing_primary_race_uses_general_development(
    monkeypatch,
) -> None:
    context = create_context()

    context.primary_race = None

    builder, _, _ = create_builder(
        context=context
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    prepared = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        trajectory_start_date=(
            TRAJECTORY_START_DATE
        ),
    )

    planning_input = prepared.planning_input

    assert planning_input.target_race_date is None
    assert planning_input.target_distance_km is None
    assert (
        planning_input.target_elevation_gain_m
        is None
    )


def test_missing_available_days_is_rejected() -> None:
    context = create_context(
        athlete=create_athlete(
            available_days=[]
        )
    )

    builder, _, _ = create_builder(
        context=context
    )

    with pytest.raises(
        WeeklyPlanningContextError,
        match="Aucun jour",
    ):
        builder.build(
            athlete_profile_id=uuid4(),
            planning_date=PLANNING_DATE,
            trajectory_start_date=(
                TRAJECTORY_START_DATE
            ),
        )


def test_missing_race_distance_is_rejected() -> None:
    context = create_context(
        primary_race=create_race(
            distance_km=None
        )
    )

    builder, _, _ = create_builder(
        context=context
    )

    with pytest.raises(
        WeeklyPlanningContextError,
        match="distance",
    ):
        builder.build(
            athlete_profile_id=uuid4(),
            planning_date=PLANNING_DATE,
            trajectory_start_date=(
                TRAJECTORY_START_DATE
            ),
        )


def test_context_services_receive_correct_dates(
    monkeypatch,
) -> None:
    builder, planning_service, history_service = (
        create_builder()
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    class FrozenDate(date):
        @classmethod
        def today(cls) -> date:
            return date(
                2026,
                8,
                26,
            )

    monkeypatch.setattr(
        "opencoach.coaching.generation.context.date",
        FrozenDate,
    )

    athlete_profile_id = uuid4()

    builder.build(
        athlete_profile_id=(
            athlete_profile_id
        ),
        planning_date=PLANNING_DATE,
        trajectory_start_date=(
            TRAJECTORY_START_DATE
        ),
    )

    assert planning_service.calls == [
        {
            "athlete_profile_id":
                athlete_profile_id,
            "planning_date":
                PLANNING_DATE,
        }
    ]

    assert history_service.calls == [
        {
            "athlete_profile_id":
                athlete_profile_id,
            "reference_date":
                date(
                    2026,
                    8,
                    26,
                ),
        }
    ]

def test_build_creates_current_week_input(
    monkeypatch,
) -> None:
    builder, _, _ = (
        create_builder()
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    result = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        trajectory_start_date=(
            TRAJECTORY_START_DATE
        ),
    )

    planning_input = (
        result.planning_input
    )

    assert (
        planning_input.planning_date
        == PLANNING_DATE
    )

    assert (
        planning_input.trajectory_start_date
        == TRAJECTORY_START_DATE
    )

    assert (
        planning_input.target_race_date
        == date(
            2027,
            9,
            18,
        )
    )

    assert (
        planning_input.target_distance_km
        == 65.0
    )

    assert (
        planning_input.target_elevation_gain_m
        == 3000.0
    )

    assert (
        planning_input.available_days
        == (
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SUNDAY,
        )
    )


def test_missing_elevation_defaults_to_zero(
    monkeypatch,
) -> None:
    context = create_context(
        primary_race=create_race(
            elevation_gain_m=None
        )
    )

    builder, _, _ = create_builder(
        context=context
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    result = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        trajectory_start_date=(
            TRAJECTORY_START_DATE
        ),
    )

    assert (
        result.planning_input
        .target_elevation_gain_m
        == 0.0
    )


def test_constraints_mark_schedule_as_constrained(
    monkeypatch,
) -> None:
    context = create_context(
        constraints=(
            object(),
        )
    )

    builder, _, _ = create_builder(
        context=context
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    result = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        trajectory_start_date=(
            TRAJECTORY_START_DATE
        ),
    )

    assert (
        result.planning_input
        .athlete_schedule_constrained
        is True
    )


def test_weekly_session_frequency_is_transmitted_to_planning_input(
    monkeypatch,
) -> None:
    """La fréquence déclarée alimente la cible hebdomadaire."""

    context = create_context(
        athlete=create_athlete(
            weekly_sessions=4,
            available_days=[
                0,
                2,
                4,
                5,
            ],
        )
    )

    builder, _, _ = create_builder(
        context=context
    )

    monkeypatch.setattr(
        "opencoach.coaching.generation.context."
        "calculate_training_history_metrics",
        lambda snapshot: create_metrics(),
    )

    prepared = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        trajectory_start_date=(
            TRAJECTORY_START_DATE
        ),
    )

    assert (
        prepared.planning_input.target_session_count
        == 4
    )

    assert (
        prepared.planning_input.available_days
        == (
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
        )
    )

def test_weekly_duration_reference_is_transmitted_to_planning_input(
    monkeypatch,
) -> None:
    builder, _, _ = create_builder()

    monkeypatch.setattr(
        "opencoach.coaching.generation.context."
        "calculate_training_history_metrics",
        lambda snapshot: create_metrics(),
    )

    prepared = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        trajectory_start_date=(
            TRAJECTORY_START_DATE
        ),
    )

    assert (
        prepared.planning_input
        .reference_weekly_duration_minutes
        == 300.0
    )

def test_general_development_context_reaches_coaching_pipeline(
    monkeypatch,
) -> None:
    context = create_context()

    context.primary_race = None

    builder, _, _ = create_builder(
        context=context
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    prepared = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        trajectory_start_date=(
            PLANNING_DATE
        ),
    )

    result = build_current_week_coaching(
        input_data=prepared.planning_input
    )

    assert result.trajectory.target_race_date is None

    assert result.trajectory.week_count == 12

    assert result.trajectory_week.phase in {
        TrainingPhase.BASE,
        TrainingPhase.BUILD,
    }

    assert all(
        week.phase
        in {
            TrainingPhase.BASE,
            TrainingPhase.BUILD,
        }
        for week in result.trajectory.weeks
    )


def test_past_planning_uses_planning_date_for_history(
    monkeypatch,
) -> None:
    builder, _, history_service = (
        create_builder()
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    class FrozenDate(date):
        @classmethod
        def today(cls) -> date:
            return date(
                2026,
                8,
                26,
            )

    monkeypatch.setattr(
        "opencoach.coaching.generation.context.date",
        FrozenDate,
    )

    athlete_profile_id = uuid4()

    past_date = date(
        2026,
        8,
        10,
    )

    builder.build(
        athlete_profile_id=athlete_profile_id,
        planning_date=past_date,
        trajectory_start_date=past_date,
    )

    assert history_service.calls == [
        {
            "athlete_profile_id":
                athlete_profile_id,
            "reference_date":
                past_date,
        }
    ]


def test_far_primary_race_stays_known_but_does_not_activate_race_planning(
    monkeypatch,
) -> None:
    far_race = create_race(
        race_date=date(
            2027,
            2,
            7,
        ),
    )

    context = create_context(
        primary_race=far_race,
    )

    builder, _, _ = create_builder(
        context=context,
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    prepared = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=date(
            2026,
            8,
            24,
        ),
        trajectory_start_date=date(
            2026,
            8,
            24,
        ),
    )

    # La course reste connue dans le contexte source.
    assert context.primary_race is far_race

    # Mais elle n'est pas encore une cible active pour le moteur.
    assert (
        prepared.planning_input.target_race_date
        is None
    )

    result = build_current_week_coaching(
        input_data=prepared.planning_input,
    )

    assert (
        result.trajectory.target_race_date
        is None
    )

    assert (
        result.trajectory.mode.value
        == "maintenance"
    )


def test_primary_race_activates_on_preparation_horizon_boundary(
    monkeypatch,
) -> None:
    race = create_race(
        race_date=date(
            2027,
            2,
            7,
        ),
    )

    context = create_context(
        primary_race=race,
    )

    builder, _, _ = create_builder(
        context=context,
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    preparation_week_start = date(
        2026,
        10,
        26,
    )

    prepared = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=preparation_week_start,
        trajectory_start_date=date(
            2026,
            8,
            24,
        ),
    )

    assert (
        prepared.planning_input.target_race_date
        == race.date
    )

    assert (
        prepared.planning_input.target_distance_km
        == race.distance_km
    )

    result = build_current_week_coaching(
        input_data=prepared.planning_input,
    )

    assert (
        result.trajectory.target_race_date
        == race.date
    )

    assert (
        result.trajectory.mode.value
        == "race_preparation"
    )


def test_race_preparation_keeps_stable_activation_anchor(
    monkeypatch,
) -> None:
    race = create_race(
        race_date=date(
            2027,
            2,
            7,
        ),
    )

    context = create_context(
        primary_race=race,
    )

    builder, _, _ = create_builder(
        context=context,
    )

    monkeypatch.setattr(
        (
            "opencoach.coaching.generation.context."
            "calculate_training_history_metrics"
        ),
        lambda snapshot: create_metrics(),
    )

    prepared = builder.build(
        athlete_profile_id=uuid4(),
        planning_date=date(
            2026,
            11,
            2,
        ),
        trajectory_start_date=date(
            2026,
            8,
            24,
        ),
    )

    assert (
        prepared.planning_input.trajectory_start_date
        == date(
            2026,
            10,
            26,
        )
    )
