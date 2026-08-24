"""Tests d'intégration d'une semaine spécifique montagneuse."""

from datetime import date

from opencoach.planning.knowledge.race_demand_profile import (
    build_race_demand_profile,
)
from opencoach.planning.stimulus.contextual_prescription import (
    build_contextual_stimulus_prescription,
)
from opencoach.planning.stimulus.weekly_demand import (
    build_weekly_stimulus_demand,
)
from opencoach.planning.sessions.intent_builder import (
    build_session_intent_plan,
)
from opencoach.planning.sessions.families import (
    session_intent_family,
)
from opencoach.planning.stimulus.families import (
    StimulusFamily,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def test_specific_mountain_week_has_single_threshold_family_intent() -> None:
    race_profile = build_race_demand_profile(
        distance_km=70.0,
        elevation_gain_m=3500.0,
    )

    prescription = build_contextual_stimulus_prescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=race_profile,
    )

    demand = build_weekly_stimulus_demand(
        prescription=prescription,
        week_type=TrajectoryWeekType.LOADING,
        target_load=185.0,
        reference_load=180.0,
    )

    plan = build_session_intent_plan(
        weekly_demand=demand
    )

    threshold_intents = tuple(
        intent
        for intent in plan.intents
        if session_intent_family(intent)
        is StimulusFamily.THRESHOLD
    )

    assert len(threshold_intents) == 1
