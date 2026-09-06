from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.database import models  # noqa: F401
from opencoach.database.base import Base
from opencoach.database.models.activity import Activity
from opencoach.database.models.activity_equipment_assignment import (
    ActivityEquipmentAssignment,
)
from opencoach.database.models.athlete_profile import AthleteProfile
from opencoach.database.models.bike import Bike
from opencoach.database.models.shoe import Shoe
from opencoach.database.models.user import User
from opencoach.equipment.mileage_service import (
    EquipmentMileageError,
    EquipmentMileageService,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        yield db

    Base.metadata.drop_all(engine)
    engine.dispose()


def _create_profile(
    session: Session,
) -> AthleteProfile:
    user = User(
        id=uuid4(),
        email=f"{uuid4()}@example.test",
    )
    session.add(user)
    session.flush()

    profile = AthleteProfile(
        id=uuid4(),
        user_id=user.id,
    )
    session.add(profile)
    session.flush()

    return profile


def _create_activity(
    session: Session,
    *,
    profile_id,
    suffix: str,
    distance_m: float,
) -> Activity:
    activity = Activity(
        id=uuid4(),
        athlete_profile_id=profile_id,
        provider="test",
        provider_activity_id=f"activity-{suffix}",
        name=f"Activity {suffix}",
        sport_type="TrailRun",
        start_at=datetime(
            2026,
            9,
            6,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        distance_m=distance_m,
    )
    session.add(activity)
    session.flush()

    return activity


def test_shoe_without_assignments_keeps_baseline(
    session: Session,
) -> None:
    profile = _create_profile(session)

    shoe = Shoe(
        id="shoe-baseline",
        athlete_profile_id=profile.id,
        model="Test Shoe",
        active=True,
        distance_km=367.0,
        baseline_distance_km=367.0,
    )
    session.add(shoe)
    session.flush()

    result = EquipmentMileageService(
        session
    ).recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=shoe.id,
    )

    assert result == pytest.approx(367.0)
    assert shoe.distance_km == pytest.approx(367.0)


def test_shoe_adds_all_assigned_distances(
    session: Session,
) -> None:
    profile = _create_profile(session)

    shoe = Shoe(
        id="shoe-sum",
        athlete_profile_id=profile.id,
        model="Test Shoe",
        active=True,
        distance_km=100.0,
        baseline_distance_km=100.0,
    )
    session.add(shoe)

    first = _create_activity(
        session,
        profile_id=profile.id,
        suffix="sum-1",
        distance_m=10000.0,
    )
    second = _create_activity(
        session,
        profile_id=profile.id,
        suffix="sum-2",
        distance_m=5500.0,
    )

    session.add_all(
        [
            ActivityEquipmentAssignment(
                athlete_profile_id=profile.id,
                activity_id=first.id,
                shoe_id=shoe.id,
                bike_id=None,
                distance_km=10.0,
                assignment_source="automatic",
            ),
            ActivityEquipmentAssignment(
                athlete_profile_id=profile.id,
                activity_id=second.id,
                shoe_id=shoe.id,
                bike_id=None,
                distance_km=5.5,
                assignment_source="manual",
            ),
        ]
    )
    session.flush()

    result = EquipmentMileageService(
        session
    ).recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=shoe.id,
    )

    assert result == pytest.approx(115.5)
    assert shoe.distance_km == pytest.approx(115.5)


def test_recalculation_is_idempotent(
    session: Session,
) -> None:
    profile = _create_profile(session)

    shoe = Shoe(
        id="shoe-idempotent",
        athlete_profile_id=profile.id,
        model="Test Shoe",
        active=True,
        distance_km=200.0,
        baseline_distance_km=200.0,
    )
    session.add(shoe)

    activity = _create_activity(
        session,
        profile_id=profile.id,
        suffix="idempotent",
        distance_m=12500.0,
    )

    session.add(
        ActivityEquipmentAssignment(
            athlete_profile_id=profile.id,
            activity_id=activity.id,
            shoe_id=shoe.id,
            bike_id=None,
            distance_km=12.5,
            assignment_source="automatic",
        )
    )
    session.flush()

    service = EquipmentMileageService(session)

    first = service.recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=shoe.id,
    )
    second = service.recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=shoe.id,
    )

    assert first == pytest.approx(212.5)
    assert second == pytest.approx(212.5)
    assert shoe.distance_km == pytest.approx(212.5)


def test_changed_assignment_distance_replaces_old_value(
    session: Session,
) -> None:
    profile = _create_profile(session)

    shoe = Shoe(
        id="shoe-update",
        athlete_profile_id=profile.id,
        model="Test Shoe",
        active=True,
        distance_km=50.0,
        baseline_distance_km=50.0,
    )
    session.add(shoe)

    activity = _create_activity(
        session,
        profile_id=profile.id,
        suffix="update",
        distance_m=10000.0,
    )

    assignment = ActivityEquipmentAssignment(
        athlete_profile_id=profile.id,
        activity_id=activity.id,
        shoe_id=shoe.id,
        bike_id=None,
        distance_km=10.0,
        assignment_source="automatic",
    )
    session.add(assignment)
    session.flush()

    service = EquipmentMileageService(session)

    assert service.recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=shoe.id,
    ) == pytest.approx(60.0)

    assignment.distance_km = 14.1
    session.flush()

    assert service.recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=shoe.id,
    ) == pytest.approx(64.1)

    assert shoe.distance_km == pytest.approx(64.1)


def test_moving_assignment_recalculates_both_shoes(
    session: Session,
) -> None:
    profile = _create_profile(session)

    first_shoe = Shoe(
        id="shoe-first",
        athlete_profile_id=profile.id,
        model="First",
        active=True,
        distance_km=100.0,
        baseline_distance_km=100.0,
    )
    second_shoe = Shoe(
        id="shoe-second",
        athlete_profile_id=profile.id,
        model="Second",
        active=True,
        distance_km=300.0,
        baseline_distance_km=300.0,
    )
    session.add_all(
        [
            first_shoe,
            second_shoe,
        ]
    )

    activity = _create_activity(
        session,
        profile_id=profile.id,
        suffix="move",
        distance_m=8000.0,
    )

    assignment = ActivityEquipmentAssignment(
        athlete_profile_id=profile.id,
        activity_id=activity.id,
        shoe_id=first_shoe.id,
        bike_id=None,
        distance_km=8.0,
        assignment_source="automatic",
    )
    session.add(assignment)
    session.flush()

    service = EquipmentMileageService(session)

    service.recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=first_shoe.id,
    )

    assert first_shoe.distance_km == pytest.approx(108.0)

    assignment.shoe_id = second_shoe.id
    session.flush()

    service.recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=first_shoe.id,
    )
    service.recalculate_shoe(
        athlete_profile_id=profile.id,
        shoe_id=second_shoe.id,
    )

    assert first_shoe.distance_km == pytest.approx(100.0)
    assert second_shoe.distance_km == pytest.approx(308.0)


def test_other_profile_assignments_are_ignored(
    session: Session,
) -> None:
    profile_a = _create_profile(session)
    profile_b = _create_profile(session)

    shoe_a = Shoe(
        id="shoe-profile-a",
        athlete_profile_id=profile_a.id,
        model="A",
        active=True,
        distance_km=10.0,
        baseline_distance_km=10.0,
    )
    shoe_b = Shoe(
        id="shoe-profile-b",
        athlete_profile_id=profile_b.id,
        model="B",
        active=True,
        distance_km=20.0,
        baseline_distance_km=20.0,
    )
    session.add_all([shoe_a, shoe_b])

    activity_b = _create_activity(
        session,
        profile_id=profile_b.id,
        suffix="profile-b",
        distance_m=9000.0,
    )

    session.add(
        ActivityEquipmentAssignment(
            athlete_profile_id=profile_b.id,
            activity_id=activity_b.id,
            shoe_id=shoe_b.id,
            bike_id=None,
            distance_km=9.0,
            assignment_source="automatic",
        )
    )
    session.flush()

    result = EquipmentMileageService(
        session
    ).recalculate_shoe(
        athlete_profile_id=profile_a.id,
        shoe_id=shoe_a.id,
    )

    assert result == pytest.approx(10.0)


def test_bike_uses_same_baseline_rule(
    session: Session,
) -> None:
    profile = _create_profile(session)

    bike = Bike(
        id="bike-test",
        athlete_profile_id=profile.id,
        model="Bike",
        active=True,
        distance_km=350.0,
        baseline_distance_km=350.0,
    )
    session.add(bike)

    activity = _create_activity(
        session,
        profile_id=profile.id,
        suffix="bike",
        distance_m=25000.0,
    )

    session.add(
        ActivityEquipmentAssignment(
            athlete_profile_id=profile.id,
            activity_id=activity.id,
            shoe_id=None,
            bike_id=bike.id,
            distance_km=25.0,
            assignment_source="automatic",
        )
    )
    session.flush()

    result = EquipmentMileageService(
        session
    ).recalculate_bike(
        athlete_profile_id=profile.id,
        bike_id=bike.id,
    )

    assert result == pytest.approx(375.0)


def test_unknown_shoe_is_rejected(
    session: Session,
) -> None:
    profile = _create_profile(session)

    with pytest.raises(
        EquipmentMileageError,
    ):
        EquipmentMileageService(
            session
        ).recalculate_shoe(
            athlete_profile_id=profile.id,
            shoe_id="missing",
        )
