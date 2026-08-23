"""Port du coach IA chargé de générer une séance concrète.

Ce module définit le contrat entre le moteur déterministe OpenCoach
et un fournisseur IA.

Le moteur Python reste responsable :
- de l'intention ;
- du jour ;
- des contraintes de durée ;
- des modalités ;
- des stimuli ;
- de la trajectoire.

L'implémentation du SessionCoachPort transforme ce cadre en
SessionProposal concrète.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from opencoach.planning.sessions.proposal import (
    SessionProposal,
)
from opencoach.planning.weekly.session_intent_slot import (
    WeeklySessionIntentSlot,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


class SessionCoachError(RuntimeError):
    """Erreur générique du coach IA de séance."""


class SessionCoachUnavailableError(
    SessionCoachError
):
    """Le fournisseur IA n'est pas disponible."""

class SessionCoachTimeoutError(
    SessionCoachError
):
    """Le fournisseur IA n'a pas répondu dans le délai imparti."""

class SessionCoachInvalidResponseError(
    SessionCoachError
):
    """Le fournisseur IA a renvoyé une réponse inexploitable."""


@dataclass(frozen=True, slots=True)
class SessionCoachRequest:
    """Contexte transmis au coach IA pour une séance."""

    phase: TrainingPhase

    slot: WeeklySessionIntentSlot

    target_load: float | None = None

    athlete_context: str | None = None

    additional_context: tuple[
        str,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if (
            self.target_load is not None
            and self.target_load < 0
        ):
            raise ValueError(
                "La charge cible ne peut pas être négative."
            )

        if (
            self.athlete_context is not None
            and not self.athlete_context.strip()
        ):
            raise ValueError(
                "Le contexte athlète ne peut pas être vide."
            )


@runtime_checkable
class SessionCoachPort(Protocol):
    """Interface implémentée par tout coach IA de séance."""

    def generate_session(
        self,
        *,
        request: SessionCoachRequest,
    ) -> SessionProposal:
        """Génère une proposition concrète de séance."""
        ...
