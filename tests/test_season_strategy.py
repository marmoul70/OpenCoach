from datetime import (
    date,
    datetime,
    timezone,
)
from uuid import uuid4

import pytest

from opencoach.planning import (
    MacrocyclePhase,
    SeasonStrategy,
    StrategyRevision,
    TrainingStimulus,
    WeekTrajectory,
)


def create_stimulus():
    return TrainingStimulus(
        stimulus_type="threshold",
        priority="high",
        target_exposure_minutes=30,
    )


def create_week(
    *,
    week_number=1,
    start_date=date(2027, 3, 1),
    end_date=date(2027, 3, 7),
    target_load=45.0,
    load_min=42.0,
    load_max=47.0,
):
    return WeekTrajectory(
        week_number=week_number,
        start_date=start_date,
        end_date=end_date,
        phase="build",
        target_load=target_load,
        load_min=load_min,
        load_max=load_max,
        target_duration_minutes=300,
        target_distance_km=45.0,
        target_elevation_gain_m=800.0,
        primary_stimuli=(
            create_stimulus(),
        ),
    )


def create_revision():
    return StrategyRevision(
        reason="initial_plan",
        created_at=datetime(
            2027,
            3,
            1,
            tzinfo=timezone.utc,
        ),
        description="Création de la stratégie initiale.",
    )


def test_week_trajectory_contains_strategy_not_sessions() -> None:
    week = create_week()

    assert week.phase == "build"

    assert week.target_load == 45.0

    assert (
        week.primary_stimuli[0].stimulus_type
        == "threshold"
    )

    assert not hasattr(
        week,
        "sessions",
    )


def test_week_load_target_must_fit_envelope() -> None:
    with pytest.raises(
        ValueError,
        match="enveloppe",
    ):
        create_week(
            target_load=50.0,
            load_min=42.0,
            load_max=47.0,
        )


def test_week_rejects_invalid_load_range() -> None:
    with pytest.raises(
        ValueError,
        match="minimale",
    ):
        create_week(
            target_load=45.0,
            load_min=50.0,
            load_max=40.0,
        )


def test_macrocycle_phase_rejects_invalid_dates() -> None:
    with pytest.raises(
        ValueError,
        match="phase",
    ):
        MacrocyclePhase(
            phase_type="build",
            start_date=date(
                2027,
                4,
                10,
            ),
            end_date=date(
                2027,
                4,
                1,
            ),
            objective="Développer le seuil.",
            primary_stimuli=(
                "threshold",
            ),
        )


def test_strategy_calculates_weeks_to_goal() -> None:
    strategy = SeasonStrategy(
        id=uuid4(),
        athlete_profile_id=uuid4(),
        planning_date=date(
            2027,
            3,
            1,
        ),
        target_race_id=uuid4(),
        target_race_date=date(
            2027,
            6,
            12,
        ),
        phases=(),
        weeks=(),
        revision=create_revision(),
        knowledge_version="2026.08",
        policy_version="1.0",
        created_at=datetime(
            2027,
            3,
            1,
            tzinfo=timezone.utc,
        ),
    )

    assert strategy.weeks_to_goal == 15


def test_strategy_exposes_current_week() -> None:
    current = create_week(
        week_number=1,
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            7,
        ),
    )

    future = create_week(
        week_number=2,
        start_date=date(
            2027,
            3,
            8,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
    )

    strategy = SeasonStrategy(
        id=uuid4(),
        athlete_profile_id=uuid4(),
        planning_date=date(
            2027,
            3,
            3,
        ),
        target_race_id=uuid4(),
        target_race_date=date(
            2027,
            6,
            12,
        ),
        phases=(),
        weeks=(
            current,
            future,
        ),
        revision=create_revision(),
        knowledge_version="2026.08",
        policy_version="1.0",
        created_at=datetime(
            2027,
            3,
            1,
            tzinfo=timezone.utc,
        ),
    )

    assert strategy.current_week is current


def test_revision_can_reference_previous_strategy() -> None:
    previous_id = uuid4()

    revision = StrategyRevision(
        reason="new_race",
        created_at=datetime(
            2027,
            1,
            15,
            tzinfo=timezone.utc,
        ),
        description=(
            "Nouvelle course prioritaire ajoutée en mai."
        ),
        previous_strategy_id=previous_id,
    )

    assert (
        revision.previous_strategy_id
        == previous_id
    )

    assert revision.reason == "new_race"
