"""Tests de classification des changements impactant le coach."""

from copy import deepcopy
from datetime import date

from opencoach.coaching.replanning import (
    PlanningChangeImpact,
    assess_profile_change,
    assess_race_change,
)
from opencoach.models import (
    AthleteProfile,
    Race,
)


def create_profile() -> AthleteProfile:
    profile = AthleteProfile()

    profile.physiology.vma = 15.0
    profile.physiology.max_heart_rate = 181
    profile.physiology.resting_heart_rate = 50
    profile.physiology.threshold_heart_rate_1 = 145
    profile.physiology.threshold_heart_rate_2 = 160

    profile.training.weekly_sessions = 4
    profile.training.weekly_duration_minutes = 360
    profile.training.weekly_distance_km = 45.0
    profile.training.available_days = [
        0,
        2,
        4,
        6,
    ]

    profile.body.weight_kg = 85.0

    return profile


def create_primary_race() -> Race:
    return Race(
        id=None,
        date=date(2026, 9, 15),
        name="Trail objectif",
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="planned",
    )


def test_identical_profile_has_no_planning_impact() -> None:
    profile = create_profile()

    assert (
        assess_profile_change(
            profile,
            deepcopy(profile),
        )
        is PlanningChangeImpact.NONE
    )


def test_vma_change_invalidates_prescription() -> None:
    before = create_profile()
    after = deepcopy(before)

    after.physiology.vma = 15.5

    assert (
        assess_profile_change(
            before,
            after,
        )
        is PlanningChangeImpact.PRESCRIPTION
    )


def test_threshold_change_invalidates_prescription() -> None:
    before = create_profile()
    after = deepcopy(before)

    after.physiology.threshold_heart_rate_2 = 163

    assert (
        assess_profile_change(
            before,
            after,
        )
        is PlanningChangeImpact.PRESCRIPTION
    )


def test_available_days_change_invalidates_week() -> None:
    before = create_profile()
    after = deepcopy(before)

    after.training.available_days = [
        0,
        1,
        4,
        6,
    ]

    assert (
        assess_profile_change(
            before,
            after,
        )
        is PlanningChangeImpact.WEEK
    )


def test_weekly_session_count_change_invalidates_week() -> None:
    before = create_profile()
    after = deepcopy(before)

    after.training.weekly_sessions = 3

    assert (
        assess_profile_change(
            before,
            after,
        )
        is PlanningChangeImpact.WEEK
    )


def test_weight_change_does_not_rebuild_training_plan() -> None:
    before = create_profile()
    after = deepcopy(before)

    after.body.weight_kg = 84.0

    assert (
        assess_profile_change(
            before,
            after,
        )
        is PlanningChangeImpact.NONE
    )


def test_primary_race_withdrawal_invalidates_trajectory() -> None:
    before = create_primary_race()
    after = deepcopy(before)

    after.status = "not_participated"

    assert (
        assess_race_change(
            before,
            after,
        )
        is PlanningChangeImpact.TRAJECTORY
    )


def test_primary_race_date_change_invalidates_trajectory() -> None:
    before = create_primary_race()
    after = deepcopy(before)

    after.date = date(2026, 10, 1)

    assert (
        assess_race_change(
            before,
            after,
        )
        is PlanningChangeImpact.TRAJECTORY
    )


def test_primary_race_distance_change_invalidates_trajectory() -> None:
    before = create_primary_race()
    after = deepcopy(before)

    after.distance_km = 65.0

    assert (
        assess_race_change(
            before,
            after,
        )
        is PlanningChangeImpact.TRAJECTORY
    )


def test_primary_race_priority_change_invalidates_trajectory() -> None:
    before = create_primary_race()
    after = deepcopy(before)

    after.priority = "training"

    assert (
        assess_race_change(
            before,
            after,
        )
        is PlanningChangeImpact.TRAJECTORY
    )


def test_race_notes_change_has_no_planning_impact() -> None:
    before = create_primary_race()
    after = deepcopy(before)

    after.notes = "Prévoir bâtons."

    assert (
        assess_race_change(
            before,
            after,
        )
        is PlanningChangeImpact.NONE
    )
