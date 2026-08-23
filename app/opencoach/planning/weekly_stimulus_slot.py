"""Créneaux hebdomadaires de stimuli d'entraînement.

Un WeeklyStimulusSlot indique quand et dans quelles conditions
un stimulus doit être placé.

Il ne contient volontairement aucune séance concrète :
le contenu de la séance appartient au coach IA.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .training_stimulus import (
    TrainingStimulusRequirement,
)


class Weekday(StrEnum):
    """Jour de la semaine utilisé par la trajectoire."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class FatigueBudget(StrEnum):
    """Fatigue acceptable générée par le créneau."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SlotImportance(StrEnum):
    """Importance structurelle du créneau dans la semaine."""

    OPTIONAL = "optional"
    SUPPORT = "support"
    KEY = "key"


@dataclass(frozen=True, slots=True)
class WeeklyStimulusSlot:
    """Créneau produit par Python pour le coach hebdomadaire.

    Python fixe ici :
    - le jour ou la fenêtre temporelle ;
    - le stimulus attendu ;
    - l'importance du créneau ;
    - la fatigue acceptable ;
    - les contraintes d'enchaînement.

    L'IA reste responsable du contenu concret de la séance.
    """

    slot_id: str

    day: Weekday

    requirement: TrainingStimulusRequirement

    importance: SlotImportance

    fatigue_budget: FatigueBudget

    duration_available_minutes: int | None = None

    preserve_next_key_session: bool = False

    preferred_recovery_before_hours: int | None = None
    preferred_recovery_after_hours: int | None = None

    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.slot_id.strip():
            raise ValueError(
                "L'identifiant du créneau ne peut pas être vide."
            )

        if (
            self.duration_available_minutes is not None
            and self.duration_available_minutes <= 0
        ):
            raise ValueError(
                "La durée disponible doit être strictement positive."
            )

        if (
            self.preferred_recovery_before_hours is not None
            and self.preferred_recovery_before_hours < 0
        ):
            raise ValueError(
                "La récupération préférée avant le créneau "
                "ne peut pas être négative."
            )

        if (
            self.preferred_recovery_after_hours is not None
            and self.preferred_recovery_after_hours < 0
        ):
            raise ValueError(
                "La récupération préférée après le créneau "
                "ne peut pas être négative."
            )

        if (
            self.requirement.duration_min_minutes is not None
            and self.duration_available_minutes is not None
            and self.requirement.duration_min_minutes
            > self.duration_available_minutes
        ):
            raise ValueError(
                "La durée disponible est insuffisante pour "
                "le stimulus demandé."
            )
