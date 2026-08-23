from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

from opencoach.planning.season.strategist_context import (
    SeasonStrategistContext,
)


JsonPrimitive = (
    str
    | int
    | float
    | bool
    | None
)

JsonValue = (
    JsonPrimitive
    | list["JsonValue"]
    | dict[str, "JsonValue"]
)


@dataclass(frozen=True)
class SeasonStrategistRequest:
    """Payload sérialisable transmis au moteur de stratégie."""

    schema_version: str

    planning: dict[
        str,
        JsonValue,
    ]

    knowledge: dict[
        str,
        JsonValue,
    ]

    instructions: dict[
        str,
        JsonValue,
    ]


def build_season_strategist_request(
    *,
    context: SeasonStrategistContext,
) -> SeasonStrategistRequest:
    """Construit le payload provider-agnostic du moteur de stratégie."""

    return SeasonStrategistRequest(
        schema_version="1.0",
        planning=_build_planning_payload(
            context
        ),
        knowledge=_build_knowledge_payload(
            context
        ),
        instructions=_build_instruction_payload(),
    )


def _build_planning_payload(
    context: SeasonStrategistContext,
) -> dict[str, JsonValue]:
    planning_input = (
        context.planning_input
    )

    athlete = planning_input.athlete
    goals = planning_input.goals

    return {
        "athlete_profile_id": _serialize_value(
            planning_input.athlete_profile_id
        ),
        "planning_date": _serialize_value(
            planning_input.planning_date
        ),
        "days_to_target_race": (
            planning_input.days_to_target_race
        ),
        "weeks_to_target_race": (
            planning_input.weeks_to_target_race
        ),
        "is_revision": (
            planning_input.is_revision
        ),
        "athlete": {
            "profile": _serialize_value(
                athlete.profile
            ),
            "baseline": _serialize_value(
                athlete.baseline
            ),
            "physiology": _serialize_value(
                athlete.physiology
            ),
        },
        "goals": {
            "target_race": _serialize_value(
                goals.target_race
            ),
            "races": _serialize_value(
                goals.all_races
            ),
            "priority_races": _serialize_value(
                goals.priority_races
            ),
        },
        "training_state": _serialize_value(
            planning_input.training_state
        ),
        "constraints": _serialize_value(
            planning_input.constraints
        ),
        "previous_strategy": _serialize_value(
            planning_input.previous_strategy
        ),
    }


def _build_knowledge_payload(
    context: SeasonStrategistContext,
) -> dict[str, JsonValue]:
    knowledge = (
        context.training_knowledge
    )

    return {
        "knowledge_base_id": (
            knowledge.knowledge_base_id
        ),
        "knowledge_version": (
            knowledge.knowledge_version
        ),
        "topics": list(
            knowledge.topics
        ),
        "applicabilities": list(
            knowledge.applicabilities
        ),
        "items": _serialize_value(
            knowledge.items
        ),
        "sources": _serialize_value(
            knowledge.sources
        ),
        "selection_reasons": _serialize_value(
            knowledge.selection_reasons
        ),
    }


def _build_instruction_payload(
) -> dict[str, JsonValue]:
    return {
        "planning_horizon": (
            "Construire une stratégie jusqu'à la course cible."
        ),
        "future_detail_policy": (
            "Ne pas générer de séances détaillées pour les "
            "semaines futures."
        ),
        "weekly_detail_policy": (
            "Décrire uniquement les phases, trajectoires de charge, "
            "stimuli et intentions hebdomadaires."
        ),
        "revision_policy": (
            "Si une stratégie précédente existe, conserver les "
            "éléments encore pertinents et déclarer explicitement "
            "chaque modification."
        ),
        "fact_policy": (
            "Ne jamais présenter une hypothèse comme un fait."
        ),
        "knowledge_policy": (
            "Utiliser uniquement les connaissances fournies dans "
            "le contexte pour justifier les décisions scientifiques."
        ),
        "output_contract": (
            "Retourner une SeasonStrategyProposal conforme "
            "au contrat OpenCoach."
        ),
    }


def _serialize_value(
    value: Any,
) -> JsonValue:
    """Convertit récursivement les objets métier en primitives JSON."""

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    if isinstance(
        value,
        UUID,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        tuple,
    ):
        return [
            _serialize_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        list,
    ):
        return [
            _serialize_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _serialize_value(
                item
            )
            for key, item in value.items()
        }

    if hasattr(
        value,
        "__dataclass_fields__",
    ):
        return {
            field_name: _serialize_value(
                getattr(
                    value,
                    field_name,
                )
            )
            for field_name
            in value.__dataclass_fields__
        }

    raise TypeError(
        "Type non sérialisable dans SeasonStrategistRequest: "
        f"{type(value).__name__}"
    )