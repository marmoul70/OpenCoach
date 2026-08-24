"""Port de génération d'une séance concrète OpenCoach.

Ce module définit le contrat utilisé pour transformer une intention
de séance déjà planifiée en séance concrète.

Le moteur Python reste responsable :
- de l'intention ;
- du jour ;
- des contraintes de durée ;
- des modalités ;
- des stimuli ;
- de la trajectoire ;
- des données physiologiques utilisables.

Une implémentation du SessionCoachPort transforme ce cadre en
SessionProposal concrète.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from opencoach.planning.physiology.snapshot import (
    PhysiologicalCalibrationSnapshot,
)
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
    """Erreur générique de génération d'une séance."""


class SessionCoachUnavailableError(
    SessionCoachError
):
    """Le fournisseur optionnel n'est pas disponible."""


class SessionCoachTimeoutError(
    SessionCoachError
):
    """Le fournisseur optionnel n'a pas répondu à temps."""


class SessionCoachInvalidResponseError(
    SessionCoachError
):
    """Le fournisseur optionnel a renvoyé une réponse invalide."""


@dataclass(frozen=True, slots=True)
class SessionCoachRequest:
    """Contexte nécessaire à la génération d'une séance."""

    phase: TrainingPhase

    slot: WeeklySessionIntentSlot

    target_load: float | None = None

    planned_duration_minutes: int | None = None

    physiology: (
        PhysiologicalCalibrationSnapshot
        | None
    ) = None

    athlete_context: str | None = None

    additional_context: tuple[
        str,
        ...,
    ] = ()

    def __post_init__(
        self,
    ) -> None:
        if (
            self.target_load is not None
            and self.target_load < 0
        ):
            raise ValueError(
                "La charge cible ne peut pas être négative."
            )

        if (
            self.planned_duration_minutes is not None
            and self.planned_duration_minutes <= 0
        ):
            raise ValueError(
                "La durée planifiée doit être "
                "strictement positive."
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
    """Interface d'un générateur de séance OpenCoach."""

    def generate_session(
        self,
        *,
        request: SessionCoachRequest,
    ) -> SessionProposal:
        """Génère une proposition concrète de séance."""
        ...