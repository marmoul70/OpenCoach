"""Modèles d'allocation des durées de séances."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AllocatedSessionDuration:
    """Durée attribuée à un créneau hebdomadaire."""

    slot_id: str

    duration_minutes: int

    def __post_init__(self) -> None:
        if not self.slot_id.strip():
            raise ValueError(
                "L'identifiant du créneau ne peut pas être vide."
            )

        if self.duration_minutes <= 0:
            raise ValueError(
                "La durée attribuée doit être strictement positive."
            )
