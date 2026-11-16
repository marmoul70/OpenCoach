"""Adaptateur conversationnel de proposition de collecte, sans écriture du profil."""

from __future__ import annotations

from typing import Any, Callable

from pydantic import Field

from opencoach.ai.tool_engine import AITool
from opencoach.coaching.profile_data_evidence import evidence_supports_profile_value
from opencoach.coaching.profile_data_proposals import AIDataProposalCreate


class ProposeProfileDataArguments(AIDataProposalCreate):
    """Schéma Coach partagé, enrichi de la preuve conversationnelle."""

    evidence: str = Field(min_length=1, max_length=200)


def build_profile_data_proposal_tool(
    proposal_creator: Callable[[AIDataProposalCreate], Any],
    user_messages: list[str],
) -> AITool:
    """Transmet une proposition validée au cas d'usage Coach."""
    user_text = "\n".join(user_messages)

    def handler(arguments: ProposeProfileDataArguments) -> dict:
        if arguments.evidence not in user_text:
            raise ValueError("La preuve ne correspond pas à un message utilisateur.")
        if not evidence_supports_profile_value(
            arguments.field_key,
            arguments.evidence,
            arguments.value,
        ):
            raise ValueError("La valeur proposée n'est pas étayée par la preuve utilisateur.")
        proposal = proposal_creator(arguments)
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
            "Soumet au Coach une proposition de donnée durable du profil à partir "
            "d'une preuve exacte issue de la conversation. Les champs et valeurs "
            "acceptés sont définis par le schéma Coach. Cet outil ne modifie jamais "
            "directement le profil : l'utilisateur doit confirmer séparément la proposition."
        ),
        arguments_model=ProposeProfileDataArguments,
        handler=handler,
    )
