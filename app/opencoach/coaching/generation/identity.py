"""Identité stable des séances générées par OpenCoach."""

from __future__ import annotations

from datetime import date


def build_planning_key(
    *,
    week_start: date,
    slot_id: str,
) -> str:
    """Construit l'identifiant stable d'un slot hebdomadaire."""

    normalized_slot_id = slot_id.strip()

    if not normalized_slot_id:
        raise ValueError(
            "L'identifiant du slot ne peut pas être vide."
        )

    return (
        f"{week_start.isoformat()}:"
        f"{normalized_slot_id}"
    )
