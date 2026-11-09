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
            "trail_running). evidence doit être une citation exacte d'un message "
            "utilisateur qui étaye chaque valeur. Cet outil ne modifie jamais le "
            "profil : l'utilisateur doit confirmer séparément la proposition."
        ),
        arguments_model=ProposeProfileDataArguments,
        handler=handler,
    )
