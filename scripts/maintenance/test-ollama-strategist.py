#!/usr/bin/env python3

"""Smoke test réel du stratège IA local OpenCoach.

Ce script appelle réellement Ollama.

Il n'appartient volontairement pas à la suite pytest :
- lent ;
- dépend d'un service externe local ;
- résultat non déterministe.
"""

from __future__ import annotations
import json

import sys
from pathlib import Path
from time import perf_counter


PROJECT_ROOT = Path(__file__).resolve().parents[2]

APP_DIR = PROJECT_ROOT / "app"
TESTS_DIR = PROJECT_ROOT / "tests"

sys.path.insert(
    0,
    str(APP_DIR),
)

sys.path.insert(
    0,
    str(TESTS_DIR),
)


from opencoach.planning import (  # noqa: E402
    OllamaSeasonStrategist,
    OllamaSeasonStrategistConfig,
    SeasonStrategistService,
)

from test_season_strategist_service import (  # noqa: E402
    create_context,
    create_policy,
)


MODEL = "Jadio/Qwen3_4b_instruct_q4km:latest"

OLLAMA_URL = "http://127.0.0.1:11434"

MAX_ATTEMPTS = 1


def print_header() -> None:
    print()
    print("=" * 72)
    print("OpenCoach — smoke test du stratège IA local")
    print("=" * 72)
    print()
    print(f"Provider : Ollama")
    print(f"Model    : {MODEL}")
    print(f"Endpoint : {OLLAMA_URL}")
    print()


def print_gate(execution) -> None:
    gate = execution.gate

    print()
    print("Gate Python")
    print("-" * 72)

    print(
        f"Accepted          : {gate.accepted}"
    )
    print(
        f"Requires revision : {gate.requires_revision}"
    )
    print(
        f"Rejected          : {gate.rejected}"
    )

    if gate.reasons:
        print()
        print("Reasons:")

        for reason in gate.reasons:
            print(
                f"  - {reason}"
            )


def print_proposal(execution) -> None:
    proposal = execution.proposal

    print()
    print("Proposition IA")
    print("-" * 72)

    print(
        f"Résumé : {proposal.summary}"
    )

    print()
    print(
        f"Phases : {len(proposal.phases)}"
    )

    for index, phase in enumerate(
        proposal.phases,
        start=1,
    ):
        print()
        print(
            f"  Phase {index}"
        )
        print(
            f"    Type      : {phase.phase_type}"
        )
        print(
            f"    Début     : {phase.start_date}"
        )
        print(
            f"    Fin       : {phase.end_date}"
        )
        print(
            f"    Objectif  : {phase.objective}"
        )


def main() -> int:
    print_header()

    context = create_context()
    policy = create_policy()

    config = OllamaSeasonStrategistConfig(
        base_url=OLLAMA_URL,
        model=MODEL,
        timeout_seconds=600.0,
        temperature=0.2,
    )

    strategist = OllamaSeasonStrategist(
        config=config,
    )

    service = SeasonStrategistService(
        strategist=strategist,
        max_attempts=MAX_ATTEMPTS,
    )

    print("Construction du contexte ........ OK")
    print("Construction de la policy ........ OK")
    print()
    print("Génération IA en cours...")
    print()

    started_at = perf_counter()

    try:
        execution = service.execute(
            context=context,
            policy=policy,
        )
    except Exception as exc:
        elapsed = perf_counter() - started_at

        print()
        print("=" * 72)
        print("ÉCHEC DU SMOKE TEST")
        print("=" * 72)
        print()
        print(
            f"Durée : {elapsed:.1f} secondes"
        )
        print(
            f"Erreur : {type(exc).__name__}: {exc}"
        )

        return 1

    elapsed = perf_counter() - started_at

    print(
        f"Génération terminée en {elapsed:.1f} secondes."
    )

    print()
    print(
        f"Modèle retourné : {execution.response.model}"
    )
    print(
        f"Tentatives      : {execution.attempt_count}"
    )

    print_proposal(
        execution
    )

    print_gate(
        execution
    )

    print()
    print("=" * 72)

    if execution.accepted:
        print("RÉSULTAT : ACCEPT")
    elif execution.requires_revision:
        print("RÉSULTAT : REVISE")
    elif execution.rejected:
        print("RÉSULTAT : REJECT")
    else:
        print("RÉSULTAT : STATUT INCONNU")

    print("=" * 72)
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )