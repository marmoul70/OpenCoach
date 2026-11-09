"""Tests de l'outil de collecte de données lié aux preuves utilisateur."""

from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from opencoach.ai.data_collection_tools import build_profile_data_proposal_tool
from opencoach.ai.tool_engine import AIToolRegistry
from opencoach.database.base import Base
from opencoach.database.models import AIDataProposal, AthleteProfile, User


def _database():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    user = User(id=uuid4(), email="data-collection@example.test")
    profile = AthleteProfile(user=user)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return engine, session, profile


def test_proposal_tool_requires_exact_user_evidence_and_creates_pending_only():
    engine, db, profile = _database()
    try:
        tool = build_profile_data_proposal_tool(
            db,
            profile.id,
            ["Ma VMA mesurée est de 15,5 km/h."],
        )
        registry = AIToolRegistry()
        registry.register(tool)

        result = registry.execute(
            "propose_profile_data",
            {
                "field_key": "vma",
                "value": 15.5,
                "evidence": "Ma VMA mesurée est de 15,5 km/h.",
            },
        )

        assert result.status == "ok"
        assert result.data["status"] == "pending"
        assert result.data["requires_explicit_confirmation"] is True
        assert result.data["unit"] == "km/h"
        assert profile.vma is None
        assert db.query(AIDataProposal).count() == 1
        assert registry.execution_results[-1].data == result.data
    finally:
        db.close()
        engine.dispose()


def test_proposal_tool_rejects_evidence_not_present_in_user_messages():
    engine, db, profile = _database()
    try:
        tool = build_profile_data_proposal_tool(
            db,
            profile.id,
            ["Je ne connais pas ma VMA."],
        )
        registry = AIToolRegistry()
        registry.register(tool)

        result = registry.execute(
            "propose_profile_data",
            {
                "field_key": "vma",
                "value": 15.5,
                "evidence": "Ma VMA est de 15,5 km/h.",
            },
        )

        assert result.status == "failed"
        assert db.query(AIDataProposal).count() == 0
        assert profile.vma is None
    finally:
        db.close()
        engine.dispose()


def test_proposal_tool_rejects_value_not_contained_in_evidence():
    engine, db, profile = _database()
    try:
        tool = build_profile_data_proposal_tool(
            db,
            profile.id,
            ["Ma VMA est de 15 km/h."],
        )
        registry = AIToolRegistry()
        registry.register(tool)

        result = registry.execute(
            "propose_profile_data",
            {
                "field_key": "vma",
                "value": 16,
                "evidence": "Ma VMA est de 15 km/h.",
            },
        )

        assert result.status == "failed"
        assert db.query(AIDataProposal).count() == 0
        assert profile.vma is None
    finally:
        db.close()
        engine.dispose()


def test_proposal_tool_uses_only_authenticated_profile_scope():
    engine, db, profile = _database()
    try:
        other_profile = AthleteProfile(
            user=User(id=uuid4(), email="other-data-collection@example.test")
        )
        db.add(other_profile)
        db.commit()

        tool = build_profile_data_proposal_tool(
            db,
            profile.id,
            ["Je pèse 82 kg."],
        )
        registry = AIToolRegistry()
        registry.register(tool)
        result = registry.execute(
            "propose_profile_data",
            {
                "field_key": "weight_kg",
                "value": 82,
                "evidence": "Je pèse 82 kg.",
            },
        )

        proposal = db.query(AIDataProposal).one()
        assert result.status == "ok"
        assert proposal.athlete_profile_id == profile.id
        assert other_profile.weight_kg is None
    finally:
        db.close()
        engine.dispose()

def test_proposal_tool_accepts_structured_days_only_when_evidence_names_each_day():
    engine, db, profile = _database()
    try:
        evidence = "Je suis disponible le lundi, mercredi et vendredi."
        tool = build_profile_data_proposal_tool(db, profile.id, [evidence])
        registry = AIToolRegistry()
        registry.register(tool)
        result = registry.execute("propose_profile_data", {
            "field_key": "available_days", "value": [0, 2, 4], "evidence": evidence,
        })
        assert result.status == "ok"
        assert result.data["value"] == [0, 2, 4]
        assert profile.available_days == []
    finally:
        db.close()
        engine.dispose()


def test_proposal_tool_rejects_structured_value_not_supported_by_evidence():
    engine, db, profile = _database()
    try:
        evidence = "Je suis disponible le lundi et le mercredi."
        tool = build_profile_data_proposal_tool(db, profile.id, [evidence])
        registry = AIToolRegistry()
        registry.register(tool)
        result = registry.execute("propose_profile_data", {
            "field_key": "available_days", "value": [0, 2, 4], "evidence": evidence,
        })
        assert result.status == "failed"
        assert db.query(AIDataProposal).count() == 0
    finally:
        db.close()
        engine.dispose()


def test_proposal_tool_accepts_experience_and_discipline_from_french_evidence():
    engine, db, profile = _database()
    try:
        evidence = "Je suis coureur intermédiaire et je pratique le trail."
        tool = build_profile_data_proposal_tool(db, profile.id, [evidence])
        registry = AIToolRegistry()
        registry.register(tool)
        experience = registry.execute("propose_profile_data", {
            "field_key": "experience", "value": "intermediate", "evidence": evidence,
        })
        discipline = registry.execute("propose_profile_data", {
            "field_key": "sport_disciplines", "value": ["trail_running"], "evidence": evidence,
        })
        assert experience.status == "ok"
        assert discipline.status == "ok"
        assert profile.experience == "beginner"
        assert profile.sport_disciplines == []
    finally:
        db.close()
        engine.dispose()

def test_equipment_proposal_requires_brand_and_model_in_exact_evidence():
    engine, db, profile = _database()
    try:
        evidence = "J'ai acheté des Asics Trabuco 14 pour le trail."
        tool = build_profile_data_proposal_tool(db, profile.id, [evidence])
        registry = AIToolRegistry()
        registry.register(tool)
        result = registry.execute("propose_profile_data", {
            "field_key": "shoe",
            "value": {"model": "Trabuco 14", "brand": "Asics", "category": "trail"},
            "evidence": evidence,
        })
        assert result.status == "ok"
        assert result.data["status"] == "pending"
        assert profile.shoes == []
    finally:
        db.close()
        engine.dispose()


def test_equipment_proposal_rejects_invented_brand():
    engine, db, profile = _database()
    try:
        evidence = "J'ai acheté des Trabuco 14."
        tool = build_profile_data_proposal_tool(db, profile.id, [evidence])
        registry = AIToolRegistry()
        registry.register(tool)
        result = registry.execute("propose_profile_data", {
            "field_key": "shoe",
            "value": {"model": "Trabuco 14", "brand": "Asics"},
            "evidence": evidence,
        })
        assert result.status == "failed"
        assert db.query(AIDataProposal).count() == 0
    finally:
        db.close()
        engine.dispose()


def test_daily_checkin_tool_requires_explicit_evidence_and_creates_pending_proposal():
    engine, db, profile = _database()
    try:
        evidence = "Énergie 3/5, douleur 4/5, pas malade, disponible, gêne au genou gauche."
        tool = build_profile_data_proposal_tool(db, profile.id, [evidence])
        registry = AIToolRegistry()
        registry.register(tool)
        result = registry.execute("propose_profile_data", {
            "field_key": "daily_checkin",
            "value": {
                "energy_rating": 3,
                "pain_wellness_rating": 4,
                "illness": False,
                "unavailable": False,
                "pain_locations": [{"area": "knee", "side": "left"}],
            },
            "evidence": evidence,
        })
        assert result.status == "ok"
        assert result.data["field_key"] == "daily_checkin"
        assert result.data["status"] == "pending"
        assert result.data["requires_explicit_confirmation"] is True
        assert db.query(AIDataProposal).count() == 1
        from opencoach.database.models.daily_checkin import DailyCheckIn
        assert db.query(DailyCheckIn).count() == 0
    finally:
        db.close()
        engine.dispose()


def test_daily_checkin_tool_rejects_missing_illness_evidence():
    engine, db, profile = _database()
    try:
        evidence = "Énergie 3/5, douleur 5/5, disponible."
        tool = build_profile_data_proposal_tool(db, profile.id, [evidence])
        registry = AIToolRegistry()
        registry.register(tool)
        result = registry.execute("propose_profile_data", {
            "field_key": "daily_checkin",
            "value": {
                "energy_rating": 3,
                "pain_wellness_rating": 5,
                "illness": False,
                "unavailable": False,
            },
            "evidence": evidence,
        })
        assert result.status == "failed"
        assert db.query(AIDataProposal).count() == 0
    finally:
        db.close()
        engine.dispose()
