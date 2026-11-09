"""Cycle sécurisé de proposition et confirmation des données de profil."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import AIDataProposal, AthleteProfile
from opencoach.schemas.profile import AthletePhysiologySchema


PROFILE_FIELD_RULES: dict[str, dict[str, Any]] = {
    "height_cm": {"unit": "cm", "kind": "float", "min": 1, "max": 250},
    "weight_kg": {"unit": "kg", "kind": "float", "min": 1, "max": 500},
    "max_heart_rate": {"unit": "bpm", "kind": "int", "min": 1, "max": 250},
    "resting_heart_rate": {"unit": "bpm", "kind": "int", "min": 1, "max": 150},
    "vma": {"unit": "km/h", "kind": "float", "min": 0.1, "max": 40},
    "threshold_heart_rate_1": {"unit": "bpm", "kind": "int", "min": 1, "max": 250},
    "threshold_heart_rate_2": {"unit": "bpm", "kind": "int", "min": 1, "max": 250},
    "weekly_sessions": {"unit": "sessions/week", "kind": "int", "min": 0, "max": None},
    "weekly_duration_minutes": {"unit": "min/week", "kind": "int", "min": 0, "max": None},
    "weekly_distance_km": {"unit": "km/week", "kind": "float", "min": 0, "max": None},
    "carbohydrates_per_hour": {"unit": "g/h", "kind": "float", "min": 0, "max": None},
    "fluids_per_hour": {"unit": "ml/h", "kind": "float", "min": 0, "max": None},
    "sodium_per_hour": {"unit": "mg/h", "kind": "float", "min": 0, "max": None},
    "fatigue_threshold": {"unit": "score", "kind": "float", "min": 0, "max": None},
}
INTEGER_FIELDS = {
    key for key, rule in PROFILE_FIELD_RULES.items() if rule["kind"] == "int"
}


class AIDataProposalCreate(BaseModel):
    """Proposition d'une valeur de profil ; aucune écriture immédiate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field_key: Literal[
        "height_cm", "weight_kg", "max_heart_rate", "resting_heart_rate",
        "vma", "threshold_heart_rate_1", "threshold_heart_rate_2",
        "weekly_sessions", "weekly_duration_minutes", "weekly_distance_km",
        "carbohydrates_per_hour", "fluids_per_hour", "sodium_per_hour",
        "fatigue_threshold",
    ]
    value: int | float

    @field_validator("value", mode="before")
    @classmethod
    def reject_boolean_and_non_numeric(cls, value: Any) -> Any:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("La valeur doit être numérique.")
        return value

    @model_validator(mode="after")
    def validate_value(self):
        rule = PROFILE_FIELD_RULES[self.field_key]
        if self.field_key in INTEGER_FIELDS and not isinstance(self.value, int):
            raise ValueError("Ce champ attend une valeur entière.")
        if self.value < rule["min"] or (rule["max"] is not None and self.value > rule["max"]):
            raise ValueError("La valeur est hors des limites autorisées.")
        return self


class AIDataProposalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    field_key: str
    value: int | float
    existing_value: int | float | None
    unit: str
    status: str
    expires_at: datetime


def _now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_response(proposal: AIDataProposal) -> AIDataProposalResponse:
    return AIDataProposalResponse(
        id=proposal.id,
        field_key=proposal.field_key,
        value=proposal.proposed_value,
        existing_value=proposal.existing_value,
        unit=proposal.unit,
        status=proposal.status,
        expires_at=proposal.expires_at,
    )


def create_profile_data_proposal(
    db: Session,
    athlete_profile_id: UUID,
    payload: AIDataProposalCreate,
) -> AIDataProposalResponse:
    profile = db.get(AthleteProfile, athlete_profile_id)
    if profile is None:
        raise LookupError("Profil sportif introuvable.")
    rule = PROFILE_FIELD_RULES[payload.field_key]
    current_value = getattr(profile, payload.field_key)
    if current_value == payload.value:
        raise ValueError("Cette valeur est déjà enregistrée dans le profil.")
    proposal = AIDataProposal(
        athlete_profile_id=athlete_profile_id,
        field_key=payload.field_key,
        proposed_value=payload.value,
        existing_value=current_value,
        unit=rule["unit"],
        status="pending",
        expires_at=_now_utc_naive() + timedelta(minutes=15),
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return _to_response(proposal)


def get_profile_data_proposal(
    db: Session,
    athlete_profile_id: UUID,
    proposal_id: UUID,
) -> AIDataProposalResponse:
    proposal = db.scalar(
        select(AIDataProposal).where(
            AIDataProposal.id == proposal_id,
            AIDataProposal.athlete_profile_id == athlete_profile_id,
        )
    )
    if proposal is None:
        raise LookupError("Proposition introuvable.")
    return _to_response(proposal)


def list_pending_profile_data_proposals(
    db: Session,
    athlete_profile_id: UUID,
    limit: int = 10,
) -> list[AIDataProposalResponse]:
    """Retourne les propositions en attente du seul profil authentifié."""
    now = _now_utc_naive()
    proposals = db.scalars(
        select(AIDataProposal)
        .where(
            AIDataProposal.athlete_profile_id == athlete_profile_id,
            AIDataProposal.status == "pending",
            AIDataProposal.expires_at > now,
        )
        .order_by(AIDataProposal.created_at.desc())
        .limit(max(1, min(limit, 20)))
    ).all()
    return [_to_response(proposal) for proposal in proposals]


def confirm_profile_data_proposal(
    db: Session,
    athlete_profile_id: UUID,
    proposal_id: UUID,
) -> AIDataProposalResponse:
    proposal = db.scalar(
        select(AIDataProposal).where(
            AIDataProposal.id == proposal_id,
            AIDataProposal.athlete_profile_id == athlete_profile_id,
        )
    )
    if proposal is None:
        raise LookupError("Proposition introuvable.")
    if proposal.status != "pending":
        raise ValueError("Cette proposition n'est plus en attente.")
    now = _now_utc_naive()
    if proposal.expires_at <= now:
        proposal.status = "expired"
        db.commit()
        raise TimeoutError("La proposition a expiré.")
    profile = db.get(AthleteProfile, athlete_profile_id)
    if profile is None:
        raise LookupError("Profil sportif introuvable.")
    current_value = getattr(profile, proposal.field_key)
    if current_value != proposal.existing_value:
        proposal.status = "conflict"
        db.commit()
        raise RuntimeError("La donnée a changé depuis la proposition ; confirmation annulée.")

    # Vérifier les contraintes physiologiques croisées avant toute écriture.
    physiology_values = {
        "max_heart_rate": profile.max_heart_rate,
        "resting_heart_rate": profile.resting_heart_rate,
        "threshold_heart_rate_1": profile.threshold_heart_rate_1,
        "threshold_heart_rate_2": profile.threshold_heart_rate_2,
        "vma": profile.vma,
    }
    if proposal.field_key in physiology_values:
        physiology_values[proposal.field_key] = proposal.proposed_value
        AthletePhysiologySchema(**physiology_values)

    setattr(profile, proposal.field_key, proposal.proposed_value)
    profile.updated_at = now
    proposal.status = "confirmed"
    proposal.confirmed_at = now
    db.commit()
    db.refresh(proposal)
    db.refresh(profile)
    if getattr(profile, proposal.field_key) != proposal.proposed_value:
        raise RuntimeError("La valeur persistée ne correspond pas à la proposition.")
    return _to_response(proposal)


def reject_profile_data_proposal(
    db: Session,
    athlete_profile_id: UUID,
    proposal_id: UUID,
) -> AIDataProposalResponse:
    proposal = db.scalar(
        select(AIDataProposal).where(
            AIDataProposal.id == proposal_id,
            AIDataProposal.athlete_profile_id == athlete_profile_id,
        )
    )
    if proposal is None:
        raise LookupError("Proposition introuvable.")
    if proposal.status != "pending":
        raise ValueError("Cette proposition n'est plus en attente.")
    proposal.status = "rejected"
    db.commit()
    db.refresh(proposal)
    return _to_response(proposal)
