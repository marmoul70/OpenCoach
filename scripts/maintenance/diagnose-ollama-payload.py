#!/usr/bin/env python3

"""Diagnostic du payload envoyé au stratège Ollama."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
TESTS_DIR = PROJECT_ROOT / "tests"

sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(TESTS_DIR))


from opencoach.planning import (  # noqa: E402
    OllamaSeasonStrategistConfig,
    build_season_strategist_request,
)
from opencoach.planning.ollama_season_strategist import (  # noqa: E402
    _build_ollama_payload,
)
from opencoach.planning.season_strategy_schema import (  # noqa: E402
    build_season_strategy_proposal_schema,
)
from test_season_strategist_service import (  # noqa: E402
    create_context,
)


MODEL = "Jadio/Qwen3_4b_instruct_q4km:latest"


def serialized_size(value: object) -> int:
    return len(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


def approximate_tokens(characters: int) -> int:
    # Diagnostic grossier uniquement.
    # Le tokenizer réel de Qwen donnera une valeur différente.
    return (characters + 3) // 4


def print_size(
    label: str,
    characters: int,
) -> None:
    print(
        f"{label:<30}"
        f"{characters:>8,} caractères"
        f"   ~{approximate_tokens(characters):>6,} tokens"
    )


def main() -> int:
    context = create_context()

    request = build_season_strategist_request(
        context=context,
    )

    config = OllamaSeasonStrategistConfig(
        model=MODEL,
    )

    payload = _build_ollama_payload(
        request=request,
        config=config,
    )

    schema = build_season_strategy_proposal_schema()

    planning_size = serialized_size(
        request.planning
    )
    knowledge_size = serialized_size(
        request.knowledge
    )
    instructions_size = serialized_size(
        request.instructions
    )
    schema_size = serialized_size(
        schema
    )

    messages = payload["messages"]

    system_message = messages[0]["content"]
    user_message = messages[1]["content"]

    system_size = len(system_message)
    user_size = len(user_message)

    input_messages_size = (
        system_size
        + user_size
    )

    duplicated_schema_estimate = (
        schema_size
    )

    optimized_input_estimate = (
        input_messages_size
        - duplicated_schema_estimate
    )

    payload_size = serialized_size(
        payload
    )

    print()
    print("=" * 78)
    print("OpenCoach — diagnostic payload Ollama")
    print("=" * 78)
    print()

    print("Composants métier")
    print("-" * 78)

    print_size(
        "Planning",
        planning_size,
    )
    print_size(
        "Knowledge",
        knowledge_size,
    )
    print_size(
        "Instructions",
        instructions_size,
    )

    print()
    print("JSON Schema")
    print("-" * 78)

    print_size(
        "Schema",
        schema_size,
    )

    print()
    print("Messages réellement envoyés")
    print("-" * 78)

    print_size(
        "System message",
        system_size,
    )
    print_size(
        "User message",
        user_size,
    )
    print_size(
        "Messages total",
        input_messages_size,
    )

    print()
    print("Payload HTTP")
    print("-" * 78)

    print_size(
        "Payload complet",
        payload_size,
    )

    print()
    print("Duplication du schema")
    print("-" * 78)

    print_size(
        "Schema dupliqué estimé",
        duplicated_schema_estimate,
    )

    print_size(
        "Messages sans duplication",
        optimized_input_estimate,
    )

    print()
    print("Contexte Ollama observé")
    print("-" * 78)
    print("Context length                4,096 tokens")

    print()
    print("ATTENTION")
    print("-" * 78)
    print(
        "Les nombres de tokens ci-dessus sont des estimations "
        "basées sur 4 caractères/token."
    )
    print(
        "Ils servent uniquement à identifier les principales "
        "sources de volume."
    )

    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )