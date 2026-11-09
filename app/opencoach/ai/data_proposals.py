"""Cycle sécurisé de proposition et confirmation des données de profil."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import AIDataProposal, AthleteProfile, Bike, Shoe, Watch
from opencoach.database.models.daily_checkin import DailyCheckIn as DailyCheckInModel
from opencoach.schemas.profile import AthletePhysiologySchema, AthleteTrainingSchema


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
    "available_days": {"unit": "jours", "kind": "available_days"},
    "experience": {"unit": "", "kind": "experience"},
    "sport_disciplines": {"unit": "", "kind": "sport_disciplines"},
    "shoe": {"unit": "équipement", "kind": "equipment"},
    "bike": {"unit": "équipement", "kind": "equipment"},
    "watch": {"unit": "équipement", "kind": "equipment"},
}
INTEGER_FIELDS = {
    key for key, rule in PROFILE_FIELD_RULES.items() if rule["kind"] == "int"
}


class EquipmentProposalValue(BaseModel):
    """Informations minimales d'un nouvel équipement."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str
    brand: str | None = None
    category: str | None = None

    @field_validator("model")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 200:
            raise ValueError("Le modèle doit contenir 1 à 200 caractères.")
        return value

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or len(value) > 100:
            raise ValueError("La marque doit contenir 1 à 100 caractères.")
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or len(value) > 50:
            raise ValueError("La catégorie doit contenir 1 à 50 caractères.")
        return value


class DailyCheckInPainLocation(BaseModel):
    """Localisation d'une douleur déclarée."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    area: Literal[
        "head", "neck", "shoulder", "back", "lower_back", "hip", "groin",
        "thigh", "knee", "calf", "shin", "ankle", "achilles", "foot", "other",
    ]
    side: Literal["left", "right", "both", "center", "not_applicable"] = "not_applicable"


class DailyCheckInProposalValue(BaseModel):
    """Check-in complet : aucune valeur booléenne ou note n'est déduite."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    energy_rating: int = Field(ge=1, le=5)
    pain_wellness_rating: int = Field(ge=1, le=5)
    illness: bool
    unavailable: bool
    pain_locations: list[DailyCheckInPainLocation] = Field(default_factory=list)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_pain_locations(self):
        if self.pain_wellness_rating == 5 and self.pain_locations:
            raise ValueError("Aucune localisation ne peut être renseignée avec une note douleur de 5.")
        if self.pain_wellness_rating < 5 and not self.pain_locations:
            raise ValueError("Une localisation est nécessaire lorsque la note douleur est inférieure à 5.")
        if self.note is not None and not self.note.strip():
            raise ValueError("La note ne peut pas être vide.")
        return self


class AIDataProposalCreate(BaseModel):
    """Proposition typée ; aucune écriture immédiate dans le profil."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field_key: Literal[
        "height_cm", "weight_kg", "max_heart_rate", "resting_heart_rate",
        "vma", "threshold_heart_rate_1", "threshold_heart_rate_2",
        "weekly_sessions", "weekly_duration_minutes", "weekly_distance_km",
        "carbohydrates_per_hour", "fluids_per_hour", "sodium_per_hour",
        "fatigue_threshold", "available_days", "experience", "sport_disciplines",
        "shoe", "bike", "watch", "daily_checkin",
    ]
    value: Any

    @field_validator("value", mode="before")
    @classmethod
    def reject_boolean_and_unsupported_types(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("Les booléens ne sont pas des valeurs de profil acceptées.")
        if not isinstance(value, (int, float, str, list, dict)):
            raise ValueError("Type de donnée non pris en charge.")
        return value

    @model_validator(mode="after")
    def validate_value(self):
        if self.field_key == "daily_checkin":
            validated = DailyCheckInProposalValue.model_validate(self.value)
            object.__setattr__(self, "value", validated.model_dump(mode="json", exclude_none=True))
            return self

        rule = PROFILE_FIELD_RULES[self.field_key]
        kind = rule["kind"]

        if kind in {"int", "float"}:
            if not isinstance(self.value, (int, float)):
                raise ValueError("Ce champ attend une valeur numérique.")
            if kind == "int" and not isinstance(self.value, int):
                raise ValueError("Ce champ attend une valeur entière.")
            if self.value < rule["min"] or (
                rule["max"] is not None and self.value > rule["max"]
            ):
                raise ValueError("La valeur est hors des limites autorisées.")
            return self

        if kind == "equipment":
            equipment = EquipmentProposalValue.model_validate(self.value)
            if self.field_key == "watch" and equipment.category is not None:
                raise ValueError("Une montre ne possède pas de catégorie dans le profil.")
            object.__setattr__(self, "value", equipment.model_dump(exclude_none=True))
        elif kind == "experience":
            validated = AthleteTrainingSchema(experience=self.value)
            object.__setattr__(self, "value", validated.experience)
        elif kind == "available_days":
            if not isinstance(self.value, list) or not self.value or any(
                isinstance(day, bool) or not isinstance(day, int)
                for day in self.value
            ):
                raise ValueError("Les jours disponibles doivent être une liste d'entiers.")
            validated = AthleteTrainingSchema(available_days=self.value)
            object.__setattr__(self, "value", validated.available_days)
        elif kind == "sport_disciplines":
            if not isinstance(self.value, list) or not self.value or any(
                not isinstance(item, str) for item in self.value
            ):
                raise ValueError("Les disciplines doivent être une liste de textes.")
            validated = AthleteTrainingSchema(sport_disciplines=self.value)
            object.__setattr__(self, "value", validated.sport_disciplines)
        return self


class AIDataProposalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    field_key: str
    value: Any
    existing_value: Any | None
    unit: str
    status: str
    expires_at: datetime


def _now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _equipment_exists(
    db: Session,
    athlete_profile_id: UUID,
    field_key: str,
    value: dict[str, str],
) -> bool:
    equipment_model = {"shoe": Shoe, "bike": Bike, "watch": Watch}[field_key]
    proposed_brand = (value.get("brand") or "").casefold()
    items = db.scalars(
        select(equipment_model).where(
            equipment_model.athlete_profile_id == athlete_profile_id,
        )
    ).all()
    return any(
        item.model.casefold() == value["model"].casefold()
        and (item.brand or "").casefold() == proposed_brand
        for item in items
    )


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
    if payload.field_key == "daily_checkin":
        checkin_date = date.today()
        if db.scalar(select(DailyCheckInModel).where(
            DailyCheckInModel.athlete_profile_id == athlete_profile_id,
            DailyCheckInModel.date == checkin_date,
        )) is not None:
            raise ValueError("Un check-in existe déjà pour aujourd'hui ; utilise le formulaire de modification.")
        now = _now_utc_naive()
        pending = db.scalar(select(AIDataProposal).where(
            AIDataProposal.athlete_profile_id == athlete_profile_id,
            AIDataProposal.field_key == "daily_checkin",
            AIDataProposal.proposed_value == payload.value,
            AIDataProposal.status == "pending",
            AIDataProposal.expires_at > now,
        ))
        if pending is not None:
            return _to_response(pending)
        proposal = AIDataProposal(
            athlete_profile_id=athlete_profile_id,
            field_key="daily_checkin",
            proposed_value=payload.value,
            existing_value=None,
            unit=f"check-in du {checkin_date.isoformat()}",
            status="pending",
            expires_at=now + timedelta(minutes=15),
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        return _to_response(proposal)
    rule = PROFILE_FIELD_RULES[payload.field_key]
    current_value = None if rule["kind"] == "equipment" else getattr(profile, payload.field_key)
    if rule["kind"] == "equipment" and _equipment_exists(
        db, athlete_profile_id, payload.field_key, payload.value
    ):
        raise ValueError("Cet équipement est déjà présent dans le profil.")
    if current_value == payload.value:
        raise ValueError("Cette valeur est déjà enregistrée dans le profil.")
    now = _now_utc_naive()
    existing_pending = db.scalar(
        select(AIDataProposal).where(
            AIDataProposal.athlete_profile_id == athlete_profile_id,
            AIDataProposal.field_key == payload.field_key,
            AIDataProposal.proposed_value == payload.value,
            AIDataProposal.status == "pending",
            AIDataProposal.expires_at > now,
        )
    )
    if existing_pending is not None:
        return _to_response(existing_pending)
    proposal = AIDataProposal(
        athlete_profile_id=athlete_profile_id,
        field_key=payload.field_key,
        proposed_value=payload.value,
        existing_value=current_value,
        unit=rule["unit"],
        status="pending",
        expires_at=now + timedelta(minutes=15),
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
    if proposal.field_key == "daily_checkin":
        checkin_date = date.today()
        if db.scalar(select(DailyCheckInModel).where(
            DailyCheckInModel.athlete_profile_id == athlete_profile_id,
            DailyCheckInModel.date == checkin_date,
        )) is not None:
            proposal.status = "conflict"
            db.commit()
            raise RuntimeError("Un check-in a été enregistré entre-temps ; confirmation annulée.")
        payload = DailyCheckInProposalValue.model_validate(proposal.proposed_value)
        checkin = DailyCheckInModel(
            athlete_profile_id=athlete_profile_id,
            date=checkin_date,
            energy_rating=payload.energy_rating,
            pain_wellness_rating=payload.pain_wellness_rating,
            illness=payload.illness,
            unavailable=payload.unavailable,
            pain_locations=[item.model_dump() for item in payload.pain_locations],
            note=payload.note,
        )
        db.add(checkin)
        proposal.status = "confirmed"
        proposal.confirmed_at = now
        db.commit()
        db.refresh(proposal)
        return _to_response(proposal)

    profile = db.get(AthleteProfile, athlete_profile_id)
    if profile is None:
        raise LookupError("Profil sportif introuvable.")
    is_equipment = proposal.field_key in {"shoe", "bike", "watch"}
    current_value = None if is_equipment else getattr(profile, proposal.field_key)
    if current_value != proposal.existing_value:
        proposal.status = "conflict"
        db.commit()
        raise RuntimeError("La donnée a changé depuis la proposition ; confirmation annulée.")

    if is_equipment and _equipment_exists(
        db, athlete_profile_id, proposal.field_key, proposal.proposed_value
    ):
        proposal.status = "conflict"
        db.commit()
        raise RuntimeError("Cet équipement a été ajouté depuis la création de la proposition.")
    if proposal.field_key in {
        "max_heart_rate", "resting_heart_rate", "threshold_heart_rate_1",
        "threshold_heart_rate_2", "vma",
    }:
        physiology_values = {
            "max_heart_rate": profile.max_heart_rate,
            "resting_heart_rate": profile.resting_heart_rate,
            "threshold_heart_rate_1": profile.threshold_heart_rate_1,
            "threshold_heart_rate_2": profile.threshold_heart_rate_2,
            "vma": profile.vma,
        }
        physiology_values[proposal.field_key] = proposal.proposed_value
        AthletePhysiologySchema(**physiology_values)

    if proposal.field_key in {"available_days", "experience", "sport_disciplines"}:
        training_values = {
            "weekly_sessions": profile.weekly_sessions,
            "weekly_duration_minutes": profile.weekly_duration_minutes,
            "weekly_distance_km": profile.weekly_distance_km,
            "available_days": profile.available_days,
            "fatigue_threshold": profile.fatigue_threshold,
            "experience": profile.experience,
            "sport_disciplines": profile.sport_disciplines,
        }
        training_values[proposal.field_key] = proposal.proposed_value
        AthleteTrainingSchema(**training_values)

    if is_equipment:
        equipment_data = proposal.proposed_value
        equipment_model = {"shoe": Shoe, "bike": Bike, "watch": Watch}[proposal.field_key]
        item = equipment_model(
            id=str(uuid4()),
            athlete_profile_id=athlete_profile_id,
            model=equipment_data["model"],
            brand=equipment_data.get("brand"),
            **(
                {"category": equipment_data.get("category")}
                if proposal.field_key in {"shoe", "bike"}
                else {}
            ),
        )
        db.add(item)
    else:
        setattr(profile, proposal.field_key, proposal.proposed_value)
    profile.updated_at = now
    proposal.status = "confirmed"
    proposal.confirmed_at = now
    db.commit()
    db.refresh(proposal)
    db.refresh(profile)
    if not is_equipment and getattr(profile, proposal.field_key) != proposal.proposed_value:
        raise RuntimeError("La valeur persistée ne correspond pas à la proposition.")
    if is_equipment and not _equipment_exists(
        db, athlete_profile_id, proposal.field_key, proposal.proposed_value
    ):
        raise RuntimeError("L'équipement n'a pas été persisté correctement.")
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
