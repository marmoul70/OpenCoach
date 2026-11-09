"""Tests du cycle de proposition et confirmation des données du profil IA."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from opencoach.ai.data_proposals import (
    AIDataProposalCreate,
    confirm_profile_data_proposal,
    create_profile_data_proposal,
    get_profile_data_proposal,
    list_pending_profile_data_proposals,
    reject_profile_data_proposal,
)
from opencoach.database.base import Base
from opencoach.database.models import AIDataProposal, AthleteProfile, User


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(id=uuid4(), email="ai-proposals@example.test")
        profile = AthleteProfile(user=user)
        session.add(profile)
        session.commit()
        session.refresh(profile)
        yield session, profile
    engine.dispose()


def test_proposal_does_not_write_until_explicit_confirmation(db):
    session, profile = db
    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="vma", value=15.5),
    )

    session.refresh(profile)
    assert proposal.status == "pending"
    assert proposal.field_key == "vma"
    assert proposal.value == 15.5
    assert proposal.unit == "km/h"
    assert profile.vma is None

    confirmed = confirm_profile_data_proposal(session, profile.id, proposal.id)
    session.refresh(profile)
    assert confirmed.status == "confirmed"
    assert profile.vma == 15.5
    assert confirmed.existing_value is None
    assert confirmed.value == 15.5


def test_proposal_requires_allowed_numeric_value_and_bounds():
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="vma", value=True)
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="vma", value=80)
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="max_heart_rate", value=181.5)
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="arbitrary_sql_field", value=1)


def test_existing_value_is_captured_and_never_overwritten_silently(db):
    session, profile = db
    profile.vma = 14.0
    session.commit()

    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="vma", value=15.0),
    )
    assert proposal.existing_value == 14.0
    assert profile.vma == 14.0

    profile.vma = 14.5
    session.commit()
    with pytest.raises(RuntimeError, match="a changé"):
        confirm_profile_data_proposal(session, profile.id, proposal.id)

    session.refresh(profile)
    stored = session.get(AIDataProposal, proposal.id)
    assert profile.vma == 14.5
    assert stored.status == "conflict"


def test_proposal_is_scoped_to_athlete_and_can_be_rejected(db):
    session, profile = db
    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="weight_kg", value=82.0),
    )
    with pytest.raises(LookupError):
        get_profile_data_proposal(session, uuid4(), proposal.id)

    rejected = reject_profile_data_proposal(session, profile.id, proposal.id)
    assert rejected.status == "rejected"
    assert profile.weight_kg is None


def test_expired_proposal_cannot_be_confirmed(db):
    session, profile = db
    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="weight_kg", value=82.0),
    )
    row = session.get(AIDataProposal, proposal.id)
    row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    session.commit()

    with pytest.raises(TimeoutError):
        confirm_profile_data_proposal(session, profile.id, proposal.id)
    session.refresh(profile)
    assert profile.weight_kg is None
    assert session.get(AIDataProposal, proposal.id).status == "expired"


def test_confirmation_rejects_incoherent_physiology_without_writing(db):
    session, profile = db
    profile.max_heart_rate = 170
    session.commit()
    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="threshold_heart_rate_2", value=180),
    )

    with pytest.raises(ValidationError):
        confirm_profile_data_proposal(session, profile.id, proposal.id)

    session.refresh(profile)
    assert profile.threshold_heart_rate_2 is None
    assert session.get(AIDataProposal, proposal.id).status == "pending"


def test_confirming_the_same_proposal_twice_is_rejected(db):
    session, profile = db
    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="weekly_sessions", value=4),
    )
    confirm_profile_data_proposal(session, profile.id, proposal.id)
    with pytest.raises(ValueError, match="plus en attente"):
        confirm_profile_data_proposal(session, profile.id, proposal.id)


def test_same_value_is_not_proposed_again(db):
    session, profile = db
    profile.vma = 15.0
    session.commit()
    with pytest.raises(ValueError, match="déjà enregistrée"):
        create_profile_data_proposal(
            session,
            profile.id,
            AIDataProposalCreate(field_key="vma", value=15.0),
        )



def test_pending_proposal_list_is_scoped_and_excludes_expired_or_resolved(db):
    session, profile = db
    first = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="vma", value=15.0),
    )
    second = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="weight_kg", value=82.0),
    )
    reject_profile_data_proposal(session, profile.id, second.id)

    proposals = list_pending_profile_data_proposals(session, profile.id)
    assert [item.id for item in proposals] == [first.id]
    assert list_pending_profile_data_proposals(session, uuid4()) == []



def test_duplicate_pending_proposal_reuses_existing_proposal(db):
    session, profile = db
    payload = AIDataProposalCreate(field_key="vma", value=15.0)
    first = create_profile_data_proposal(session, profile.id, payload)
    second = create_profile_data_proposal(session, profile.id, payload)

    assert second.id == first.id
    assert session.query(AIDataProposal).count() == 1

def test_structured_training_profile_proposals_are_validated_and_confirmed(db):
    session, profile = db
    days = create_profile_data_proposal(session, profile.id, AIDataProposalCreate(field_key="available_days", value=[0, 2, 4]))
    experience = create_profile_data_proposal(session, profile.id, AIDataProposalCreate(field_key="experience", value="intermediate"))
    disciplines = create_profile_data_proposal(session, profile.id, AIDataProposalCreate(field_key="sport_disciplines", value=["road_running", "trail_running"]))

    assert days.value == [0, 2, 4]
    assert days.unit == "jours"
    assert profile.available_days == []
    assert confirm_profile_data_proposal(session, profile.id, days.id).status == "confirmed"
    assert confirm_profile_data_proposal(session, profile.id, experience.id).status == "confirmed"
    assert confirm_profile_data_proposal(session, profile.id, disciplines.id).status == "confirmed"

    session.refresh(profile)
    assert profile.available_days == [0, 2, 4]
    assert profile.experience == "intermediate"
    assert profile.sport_disciplines == ["road_running", "trail_running"]


def test_structured_training_profile_rejects_invalid_values():
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="available_days", value=[0, 7])
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="available_days", value=[1, 1])
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="available_days", value=[True])
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="experience", value="professional")
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="sport_disciplines", value=["cycling"])
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="sport_disciplines", value=["trail_running", "trail_running"])


def test_structured_training_proposal_detects_conflict_before_confirmation(db):
    session, profile = db
    proposal = create_profile_data_proposal(session, profile.id, AIDataProposalCreate(field_key="available_days", value=[1, 3]))
    profile.available_days = [0]
    session.commit()

    with pytest.raises(RuntimeError, match="a changé"):
        confirm_profile_data_proposal(session, profile.id, proposal.id)
    session.refresh(profile)
    assert profile.available_days == [0]
    assert session.get(AIDataProposal, proposal.id).status == "conflict"


def test_structured_training_profile_rejects_empty_collection_values():
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="available_days", value=[])
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="sport_disciplines", value=[])

def test_equipment_proposal_creates_item_only_after_confirmation(db):
    from opencoach.database.models import Shoe

    session, profile = db
    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(
            field_key="shoe",
            value={"model": "Trabuco 14", "brand": "Asics", "category": "trail"},
        ),
    )

    assert proposal.status == "pending"
    assert proposal.unit == "équipement"
    assert session.query(Shoe).filter_by(athlete_profile_id=profile.id).count() == 0

    confirmed = confirm_profile_data_proposal(session, profile.id, proposal.id)
    session.refresh(profile)
    assert confirmed.status == "confirmed"
    shoe = session.query(Shoe).filter_by(athlete_profile_id=profile.id).one()
    assert shoe.model == "Trabuco 14"
    assert shoe.brand == "Asics"
    assert shoe.category == "trail"
    assert shoe.active is True
    assert shoe.distance_km == 0


def test_equipment_proposal_rejects_invalid_or_duplicate_equipment(db):
    session, profile = db
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="shoe", value={"model": "", "brand": "Asics"})
    with pytest.raises(ValidationError):
        AIDataProposalCreate(field_key="watch", value={"model": "Pace 4", "category": "GPS"})

    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="watch", value={"model": "Pace 4", "brand": "COROS"}),
    )
    confirm_profile_data_proposal(session, profile.id, proposal.id)
    with pytest.raises(ValueError, match="déjà présent"):
        create_profile_data_proposal(
            session,
            profile.id,
            AIDataProposalCreate(field_key="watch", value={"model": "Pace 4", "brand": "COROS"}),
        )


def test_equipment_proposal_detects_duplicate_added_before_confirmation(db):
    from opencoach.database.models import Shoe

    session, profile = db
    proposal = create_profile_data_proposal(
        session,
        profile.id,
        AIDataProposalCreate(field_key="shoe", value={"model": "Trabuco 14", "brand": "Asics"}),
    )
    session.add(Shoe(
        id="existing-shoe",
        athlete_profile_id=profile.id,
        model="Trabuco 14",
        brand="Asics",
    ))
    session.commit()

    with pytest.raises(RuntimeError, match="ajouté depuis"):
        confirm_profile_data_proposal(session, profile.id, proposal.id)
    assert session.get(AIDataProposal, proposal.id).status == "conflict"
    assert session.query(Shoe).filter_by(athlete_profile_id=profile.id).count() == 1
