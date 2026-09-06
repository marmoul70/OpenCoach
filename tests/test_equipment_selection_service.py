from uuid import uuid4

from opencoach.equipment.activity_classification import (
    ActivityEquipmentCategory,
)
from opencoach.equipment.selection_service import (
    EquipmentSelectionService,
)
from opencoach.models.profile import Shoe


def shoe(
    *,
    category: str,
    preferred: bool = False,
    active: bool = True,
    model: str,
) -> Shoe:
    return Shoe(
        id=uuid4(),
        brand="Test",
        model=model,
        active=active,
        category=category,
        preferred=preferred,
        distance_km=0.0,
        warning_distance_km=500.0,
        max_distance_km=1000.0,
    )


def test_trail_selects_preferred_trail_shoe() -> None:
    trail = shoe(
        category="trail",
        preferred=True,
        model="Trail",
    )
    road = shoe(
        category="road",
        preferred=True,
        model="Road",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.TRAIL_RUNNING
        ),
        shoes=[road, trail],
    )

    assert selected is trail


def test_road_selects_preferred_road_shoe() -> None:
    trail = shoe(
        category="trail",
        preferred=True,
        model="Trail",
    )
    road = shoe(
        category="road",
        preferred=True,
        model="Road",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.ROAD_RUNNING
        ),
        shoes=[trail, road],
    )

    assert selected is road


def test_trail_never_selects_road_shoe() -> None:
    road = shoe(
        category="road",
        preferred=True,
        model="Road",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.TRAIL_RUNNING
        ),
        shoes=[road],
    )

    assert selected is None


def test_road_never_selects_trail_shoe() -> None:
    trail = shoe(
        category="trail",
        preferred=True,
        model="Trail",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.ROAD_RUNNING
        ),
        shoes=[trail],
    )

    assert selected is None


def test_trail_uses_preferred_mixed_as_fallback() -> None:
    mixed = shoe(
        category="mixed",
        preferred=True,
        model="Mixed",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.TRAIL_RUNNING
        ),
        shoes=[mixed],
    )

    assert selected is mixed


def test_road_uses_preferred_mixed_as_fallback() -> None:
    mixed = shoe(
        category="mixed",
        preferred=True,
        model="Mixed",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.ROAD_RUNNING
        ),
        shoes=[mixed],
    )

    assert selected is mixed


def test_single_active_trail_is_selected_without_preference() -> None:
    trail = shoe(
        category="trail",
        preferred=False,
        model="Trail",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.TRAIL_RUNNING
        ),
        shoes=[trail],
    )

    assert selected is trail


def test_ambiguous_trail_shoes_are_not_guessed() -> None:
    first = shoe(
        category="trail",
        model="Trail 1",
    )
    second = shoe(
        category="trail",
        model="Trail 2",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.TRAIL_RUNNING
        ),
        shoes=[first, second],
    )

    assert selected is None


def test_inactive_preferred_shoe_is_never_selected() -> None:
    inactive = shoe(
        category="trail",
        preferred=True,
        active=False,
        model="Inactive",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.TRAIL_RUNNING
        ),
        shoes=[inactive],
    )

    assert selected is None


def test_non_running_activity_has_no_shoe() -> None:
    road = shoe(
        category="road",
        preferred=True,
        model="Road",
    )

    selected = EquipmentSelectionService().select_shoe(
        activity_category=(
            ActivityEquipmentCategory.CYCLING
        ),
        shoes=[road],
    )

    assert selected is None
