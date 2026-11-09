"""Outil IA de proposition de collecte, sans écriture du profil."""

from __future__ import annotations

import re
from typing import Literal
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
        "fatigue_threshold",
    ]
    value: int | float
    evidence: str = Field(min_length=1, max_length=200)


def _evidence_contains_value(evidence: str, value: int | float) -> bool:
    """Vérifie que la valeur proposée apparaît littéralement dans la citation."""
    normalized = evidence.replace(",", ".")
    candidates = re.findall(r"(?<!\d)\d+(?:\.\d+)?(?!\d)", normalized)
    try:
        return any(float(candidate) == float(value) for candidate in candidates)
    except (TypeError, ValueError):
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
        if not _evidence_contains_value(arguments.evidence, arguments.value):
            raise ValueError("La valeur n'apparaît pas dans la preuve utilisateur.")
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
            "Crée une proposition de sauvegarde en attente pour une donnée durable "
            "du profil sportif uniquement lorsque l'utilisateur a explicitement "
            "fourni cette valeur. evidence doit être une citation exacte d'un message "
            "utilisateur contenant la valeur. Cet outil ne modifie jamais le profil : "
            "il crée seulement une proposition que l'utilisateur devra confirmer "
            "séparément. Ne l'utilise pas pour une valeur supposée ou déduite."
        ),
        arguments_model=ProposeProfileDataArguments,
        handler=handler,
    )
