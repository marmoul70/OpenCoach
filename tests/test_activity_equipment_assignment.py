from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.database.base import Base
from opencoach.database import models  # noqa: F401
from opencoach.database.models.activity import (
    Activity,
)
from opencoach.database.models.athlete_profile import (
    AthleteProfile,
)
from opencoach.database.models.shoe import (
    Shoe,
)
from opencoach.database.repositories.sql_activity_equipment_assignment import (
    ActivityEquipmentAssignmentError,
    SqlActivityEquipmentAssignmentRepository,
)


def create_profile(
    db: Session,
):
    profile = AthleteProfile(
        id=uuid4(),
        user_id=uuid4(),
    )
    db.add(profile)
    db.flush()
    return profile


def create_activity(
    db: Session,
    *,
    athlete_profile_id,
):
    activity = Activity(
        id=uuid4(),
        athlete_profile_id=athlete_profile_id,
        provider="test",
        provider_activity_id=str(uuid4()),
        name="Sortie",
        sport_type="Run",
        start_at=datetime.now(timezone.utc),
    )
    db.add(activity)
    db.flush()
    return activity


def create_shoe(
    db: Session,
    *,
    athlete_profile_id,
    shoe_id: str,
):
    shoe = Shoe(
        id=shoe_id,
        athlete_profile_id=athlete_profile_id,
        model="Test",
        active=True,
        preferred=True,
        distance_km=0.0,
    )
    db.add(shoe)
    db.flush()
    return shoe


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test_assign_shoe_creates_assignment(
    db: Session,
) -> None:
    profile = create_profile(db)
    activity = create_activity(
        db,
        athlete_profile_id=profile.id,
    )
    shoe = create_shoe(
        db,
        athlete_profile_id=profile.id,
        shoe_id="shoe-1",
    )

    repository = (
        SqlActivityEquipmentAssignmentRepository(
            db
        )
    )

    assignment = repository.assign_shoe(
        athlete_profile_id=profile.id,
        activity_id=activity.id,
        shoe_id=shoe.id,
        distance_km=12.4,
        assignment_source="manual",
    )

    assert assignment.shoe_id == "shoe-1"
    assert assignment.bike_id is None
    assert assignment.distance_km == 12.4
    assert assignment.assignment_source == "manual"


def test_assigning_same_activity_is_idempotent(
    db: Session,
) -> None:
    profile = create_profile(db)
    activity = create_activity(
        db,
        athlete_profile_id=profile.id,
    )

    first_shoe = create_shoe(
        db,
        athlete_profile_id=profile.id,
        shoe_id="shoe-1",
    )

    second_shoe = create_shoe(
        db,
        athlete_profile_id=profile.id,
        shoe_id="shoe-2",
    )

    repository = (
        SqlActivityEquipmentAssignmentRepository(
            db
        )
    )

    first = repository.assign_shoe(
        athlete_profile_id=profile.id,
        activity_id=activity.id,
        shoe_id=first_shoe.id,
        distance_km=10.0,
        assignment_source="automatic",
    )

    first_id = first.id

    second = repository.assign_shoe(
        athlete_profile_id=profile.id,
        activity_id=activity.id,
        shoe_id=second_shoe.id,
        distance_km=10.3,
        assignment_source="manual",
    )

    assert second.id == first_id
    assert second.shoe_id == "shoe-2"
    assert second.distance_km == 10.3
    assert second.assignment_source == "manual"

    rows = db.query(
        type(second)
    ).all()

    assert len(rows) == 1


def test_cannot_use_shoe_from_another_profile(
    db: Session,
) -> None:
    owner = create_profile(db)
    other = create_profile(db)

    activity = create_activity(
        db,
        athlete_profile_id=owner.id,
    )

    shoe = create_shoe(
        db,
        athlete_profile_id=other.id,
        shoe_id="other-shoe",
    )

    repository = (
        SqlActivityEquipmentAssignmentRepository(
            db
        )
    )

    with pytest.raises(
        ActivityEquipmentAssignmentError,
        match="Chaussure introuvable",
    ):
        repository.assign_shoe(
            athlete_profile_id=owner.id,
            activity_id=activity.id,
            shoe_id=shoe.id,
            distance_km=5.0,
            assignment_source="manual",
        )
