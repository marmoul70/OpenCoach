from datetime import datetime, timezone

import pytest

from opencoach.equipment.activity_classification import (
    ActivityEquipmentCategory,
    classify_activity,
    classify_sport_type,
)
from opencoach.models.activity import Activity


@pytest.mark.parametrize(
    ("sport_type", "expected"),
    [
        (
            "TrailRun",
            ActivityEquipmentCategory.TRAIL_RUNNING,
        ),
        (
            "Run",
            ActivityEquipmentCategory.ROAD_RUNNING,
        ),
        (
            "Ride",
            ActivityEquipmentCategory.CYCLING,
        ),
        (
            "VirtualRide",
            ActivityEquipmentCategory.CYCLING,
        ),
        (
            "Workout",
            ActivityEquipmentCategory.OTHER,
        ),
        (
            "Walk",
            ActivityEquipmentCategory.OTHER,
        ),
        (
            "Soccer",
            ActivityEquipmentCategory.OTHER,
        ),
        (
            "Swim",
            ActivityEquipmentCategory.OTHER,
        ),
        (
            "WeightTraining",
            ActivityEquipmentCategory.OTHER,
        ),
    ],
)
def test_classify_sport_type(
    sport_type: str,
    expected: ActivityEquipmentCategory,
) -> None:
    assert classify_sport_type(sport_type) is expected


def test_unknown_sport_type_is_other() -> None:
    assert (
        classify_sport_type("SomethingElse")
        is ActivityEquipmentCategory.OTHER
    )


def test_sport_type_whitespace_is_ignored() -> None:
    assert (
        classify_sport_type("  TrailRun  ")
        is ActivityEquipmentCategory.TRAIL_RUNNING
    )


def test_classify_activity_uses_open_coach_activity() -> None:
    activity = Activity(
        provider="test-provider",
        provider_activity_id="activity-1",
        name="Sortie trail",
        sport_type="TrailRun",
        start_at=datetime.now(timezone.utc),
    )

    assert (
        classify_activity(activity)
        is ActivityEquipmentCategory.TRAIL_RUNNING
    )
