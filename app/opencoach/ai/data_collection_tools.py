"""Outil IA de proposition de collecte, sans écriture du profil."""

from __future__ import annotations

import re
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.data_proposals import (
    AIDataProposalCreate,
    create_profile_data_proposal,
)
from opencoach.ai.tool_engine import AITool
from sqlalchemy.orm import Session


class ProposeProfileDataArguments(BaseModel):
    """La preuve doit être une citation exacte d'un message utilisateur."""

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
    evidence: str = Field(min_length=1, max_length=200)


_DAY_EVIDENCE = {
    0: ("lundi", "lun"),
    1: ("mardi", "mar"),
    2: ("mercredi", "mer"),
    3: ("jeudi", "jeu"),
    4: ("vendredi", "ven"),
    5: ("samedi", "sam"),
    6: ("dimanche", "dim"),
}
_DISCIPLINE_EVIDENCE = {
    "road_running": ("course sur route", "course à pied", "route"),
    "trail_running": ("trail", "course nature", "course en sentier"),
}
_EXPERIENCE_EVIDENCE = {
    "beginner": ("débutant", "débutante", "commence"),
    "intermediate": ("intermédiaire",),
    "advanced": ("avancé", "avancée", "confirmé", "confirmée"),
    "expert": ("expert", "experte"),
}


def _evidence_contains_value(
    field_key: str,
    evidence: str,
    value: Any,
) -> bool:
    """Vérifie que chaque valeur proposée est étayée dans la citation exacte."""
    normalized = evidence.casefold().replace(",", ".")
    if field_key in {
        "height_cm", "weight_kg", "max_heart_rate", "resting_heart_rate",
        "vma", "threshold_heart_rate_1", "threshold_heart_rate_2",
        "weekly_sessions", "weekly_duration_minutes", "weekly_distance_km",
        "carbohydrates_per_hour", "fluids_per_hour", "sodium_per_hour",
        "fatigue_threshold",
    }:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        candidates = re.findall(r"(?<!\d)\d+(?:\.\d+)?(?!\d)", normalized)
        try:
            return any(float(candidate) == float(value) for candidate in candidates)
        except (TypeError, ValueError):
            return False

    if field_key == "available_days" and isinstance(value, list):
        return all(
            isinstance(day, int)
            and 0 <= day <= 6
            and any(term in normalized for term in _DAY_EVIDENCE[day])
            for day in value
        )

    if field_key == "sport_disciplines" and isinstance(value, list):
        return all(
            isinstance(item, str)
            and item in _DISCIPLINE_EVIDENCE
            and any(term in normalized for term in _DISCIPLINE_EVIDENCE[item])
            for item in value
        )

    if field_key == "experience" and isinstance(value, str):
        return value in _EXPERIENCE_EVIDENCE and any(
            term in normalized for term in _EXPERIENCE_EVIDENCE[value]
        )


    if field_key == "daily_checkin" and isinstance(value, dict):
        required = {"energy_rating", "pain_wellness_rating", "illness", "unavailable"}
        if not required.issubset(value):
            return False
        if not any(term in normalized for term in ("énergie", "forme", "fatigue", "fatigué", "fatiguée")):
            return False
        if not any(term in normalized for term in ("douleur", "confort", "gêne", "gene")):
            return False
        for key in ("energy_rating", "pain_wellness_rating"):
            number = value.get(key)
            if isinstance(number, bool) or not isinstance(number, int) or str(number) not in normalized:
                return False
        illness_terms = ("malade", "maladie", "fièvre", "symptôme")
        illness_negative = ("pas malade", "aucun symptôme", "sans symptôme")
        availability_terms = ("indisponible", "pas disponible", "je ne peux pas")
        availability_negative = ("disponible", "je peux m'entraîner", "je peux courir")
        if value["illness"] is False:
            if not any(term in normalized for term in illness_negative):
                return False
        elif any(term in normalized for term in illness_negative) or not any(
            term in normalized for term in illness_terms
        ):
            return False
        if value["unavailable"] is False:
            if "pas disponible" in normalized or "indisponible" in normalized or not any(
                term in normalized for term in availability_negative
            ):
                return False
        elif not any(term in normalized for term in availability_terms):
            return False
        aliases = {
            "head": ("tête", "tete"), "neck": ("cou",), "shoulder": ("épaule", "epaule"),
            "back": ("dos",), "lower_back": ("bas du dos", "lombaire"),
            "hip": ("hanche",), "groin": ("aine",), "thigh": ("cuisse",),
            "knee": ("genou",), "calf": ("mollet",), "shin": ("tibia",),
            "ankle": ("cheville",), "achilles": ("achille",), "foot": ("pied",),
            "other": ("autre",),
        }
        for location in value.get("pain_locations", []):
            if not isinstance(location, dict) or location.get("area") not in aliases:
                return False
            if not any(term in normalized for term in aliases[location["area"]]):
                return False
            side_terms = {
                "left": ("gauche",), "right": ("droit", "droite"),
                "both": ("deux côtés", "des deux côtés", "bilatéral"),
                "center": ("au centre", "central"), "not_applicable": ("sans latéralité", "non applicable", "pas de côté précisé"),
            }
            side = location.get("side", "not_applicable")
            if side not in side_terms or (side_terms[side] and not any(term in normalized for term in side_terms[side])):
                return False
        note = value.get("note")
        if note is not None and (not isinstance(note, str) or note.casefold() not in normalized):
            return False
        return True

    if field_key in {"shoe", "bike", "watch"} and isinstance(value, dict):
        allowed_keys = {"model", "brand"} if field_key == "watch" else {"model", "brand", "category"}
        if set(value) - allowed_keys or not isinstance(value.get("model"), str):
            return False
        evidence_values = [value["model"]]
        evidence_values.extend(
            item for item in (value.get("brand"), value.get("category"))
            if item is not None
        )
        return all(
            isinstance(item, str)
            and item.strip()
            and item.casefold() in normalized
            for item in evidence_values
        )
    return False


def build_profile_data_proposal_tool(
    db: Session,
    athlete_profile_id: UUID,
    user_messages: list[str],
) -> AITool:
    """Construit un outil limité au profil authentifié et à la preuve utilisateur."""
    user_text = "\n".join(user_messages)

    def handler(arguments: ProposeProfileDataArguments) -> dict:
        if arguments.evidence not in user_text:
            raise ValueError("La preuve ne correspond pas à un message utilisateur.")
        if not _evidence_contains_value(
            arguments.field_key,
            arguments.evidence,
            arguments.value,
        ):
            raise ValueError("La valeur proposée n'est pas étayée par la preuve utilisateur.")
        proposal = create_profile_data_proposal(
            db,
            athlete_profile_id,
            AIDataProposalCreate(
                field_key=arguments.field_key,
                value=arguments.value,
            ),
        )
        return {
            "proposal_id": str(proposal.id),
            "field_key": proposal.field_key,
            "value": proposal.value,
            "existing_value": proposal.existing_value,
            "unit": proposal.unit,
            "status": proposal.status,
            "expires_at": proposal.expires_at.isoformat(),
            "requires_explicit_confirmation": True,
        }

    return AITool(
        name="propose_profile_data",
        description=(
            "Crée une proposition en attente pour une donnée durable du profil. "
            "Champs pris en charge : valeurs numériques de profil, available_days "
            "(liste de jours, lundi=0 à dimanche=6), experience (beginner, "
            "intermediate, advanced, expert), sport_disciplines (road_running, "
            "trail_running). daily_checkin attend energy_rating et pain_wellness_rating " 
            "(1 à 5), illness et unavailable explicitement déclarés, ainsi que les zones " 
            "douloureuses si pain_wellness_rating est inférieur à 5. La date est celle du jour. " 
            "Les équipements shoe, bike et watch attendent un objet "
            "avec model obligatoire, brand optionnelle et category optionnelle (pas "
            "de category pour watch). Chaque valeur textuelle doit figurer dans "
            "evidence. Cet outil ne modifie jamais le profil : l'utilisateur doit "
            "confirmer séparément la proposition."
        ),
        arguments_model=ProposeProfileDataArguments,
        handler=handler,
    )
