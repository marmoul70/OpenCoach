from datetime import datetime, timezone
from uuid import uuid4

from opencoach.equipment.activity_classification import (
    ActivityEquipmentCategory,
)
from opencoach.equipment.proposal_service import (
    EquipmentProposalService,
)
from opencoach.models.activity import Activity
from opencoach.models.profile import Shoe


def activity(
    sport_type: str,
) -> Activity:
    return Activity(
        provider="test",
        provider_activity_id=str(uuid4()),
        name="Activité test",
        sport_type=sport_type,
        start_at=datetime.now(timezone.utc),
    )


def shoe(
    *,
    shoe_id: str,
    category: str,
    preferred: bool = False,
    active: bool = True,
) -> Shoe:
    return Shoe(
        id=shoe_id,
        brand="Test",
        model=shoe_id,
        active=active,
        category=category,
        preferred=preferred,
        distance_km=0.0,
        warning_distance_km=500.0,
        max_distance_km=1000.0,
    )


def test_trail_proposes_preferred_trail() -> None:
    shoes = [
        shoe(
            shoe_id="road",
            category="road",
            preferred=True,
        ),
        shoe(
            shoe_id="trail",
            category="trail",
            preferred=True,
        ),
        shoe(
            shoe_id="mixed",
            category="mixed",
        ),
    ]

    proposal = EquipmentProposalService().propose_shoe(
        activity=activity("TrailRun"),
        shoes=shoes,
    )

    assert (
        proposal.activity_category
        is ActivityEquipmentCategory.TRAIL_RUNNING
    )
    assert proposal.selected_shoe_id == "trail"
    assert proposal.compatible_shoe_ids == (
        "trail",
        "mixed",
    )


def test_run_proposes_preferred_road() -> None:
    shoes = [
        shoe(
            shoe_id="trail",
            category="trail",
            preferred=True,
        ),
        shoe(
            shoe_id="road",
            category="road",
            preferred=True,
        ),
    ]

    proposal = EquipmentProposalService().propose_shoe(
        activity=activity("Run"),
        shoes=shoes,
    )

    assert (
        proposal.activity_category
        is ActivityEquipmentCategory.ROAD_RUNNING
    )
    assert proposal.selected_shoe_id == "road"
    assert proposal.compatible_shoe_ids == (
        "road",
    )


def test_mixed_is_compatible_with_trail_and_run() -> None:
    mixed = shoe(
        shoe_id="mixed",
        category="mixed",
        preferred=True,
    )

    trail = EquipmentProposalService().propose_shoe(
        activity=activity("TrailRun"),
        shoes=[mixed],
    )

    road = EquipmentProposalService().propose_shoe(
        activity=activity("Run"),
        shoes=[mixed],
    )

    assert trail.selected_shoe_id == "mixed"
    assert road.selected_shoe_id == "mixed"


def test_inactive_shoe_is_not_compatible() -> None:
    inactive = shoe(
        shoe_id="trail",
        category="trail",
        preferred=True,
        active=False,
    )

    proposal = EquipmentProposalService().propose_shoe(
        activity=activity("TrailRun"),
        shoes=[inactive],
    )

    assert proposal.selected_shoe_id is None
    assert proposal.compatible_shoe_ids == ()


def test_non_running_activity_has_no_shoe_proposal() -> None:
    road = shoe(
        shoe_id="road",
        category="road",
        preferred=True,
    )

    proposal = EquipmentProposalService().propose_shoe(
        activity=activity("VirtualRide"),
        shoes=[road],
    )

    assert (
        proposal.activity_category
        is ActivityEquipmentCategory.CYCLING
    )
    assert proposal.selected_shoe_id is None
    assert proposal.compatible_shoe_ids == ()
