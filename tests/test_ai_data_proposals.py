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
