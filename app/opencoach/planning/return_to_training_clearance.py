"""Décision déterministe de sortie de la phase de reprise.

Ce module ne réalise aucun diagnostic médical. Il applique les
garde-fous déclaratifs nécessaires avant de permettre au moteur
de réintégrer la trajectoire d'entraînement planifiée.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

class ReadinessAnswer(StrEnum):
    """Réponse déclarative utilisée pour la reprise."""

    UNKNOWN = "unknown"
    YES = "yes"
    NO = "no"

@dataclass(frozen=True, slots=True)
class ReturnToTrainingReadiness:
    """État déclaré utilisé pour évaluer la sortie de reprise."""

    blocking_symptoms: ReadinessAnswer = ReadinessAnswer.UNKNOWN

    recovery_sufficient: ReadinessAnswer = ReadinessAnswer.UNKNOWN

    clearance_confirmed: ReadinessAnswer = ReadinessAnswer.UNKNOWN

@dataclass(frozen=True, slots=True)
class ReturnToTrainingClearance:
    """Décision de sortie de la phase de reprise."""

    allowed: bool

    reasons: tuple[str, ...] = ()


def evaluate_return_to_training_clearance(
    *,
    minimum_completed: bool,
    requires_clearance: bool,
    readiness: ReturnToTrainingReadiness,
) -> ReturnToTrainingClearance:
    """Évalue si la trajectoire normale peut être réintégrée."""

    reasons: list[str] = []

    if not minimum_completed:
        reasons.append(
            "La durée minimale de reprise n'est pas terminée."
        )

    if readiness.blocking_symptoms is ReadinessAnswer.YES:
        reasons.append(
            "Des symptômes bloquants sont encore déclarés."
        )

    elif readiness.blocking_symptoms is ReadinessAnswer.UNKNOWN:
        reasons.append(
            "L'état des symptômes n'est pas renseigné."
        )

    if readiness.recovery_sufficient is ReadinessAnswer.NO:
        reasons.append(
            "La récupération déclarée est insuffisante."
        )

    elif readiness.recovery_sufficient is ReadinessAnswer.UNKNOWN:
        reasons.append(
            "Le niveau de récupération n'est pas renseigné."
        )

    if requires_clearance:
        if readiness.clearance_confirmed is ReadinessAnswer.NO:
            reasons.append(
                "La validation nécessaire à la reprise "
                "n'est pas confirmée."
            )

        elif readiness.clearance_confirmed is ReadinessAnswer.UNKNOWN:
            reasons.append(
                "La validation nécessaire à la reprise "
                "n'est pas renseignée."
            )

    return ReturnToTrainingClearance(
        allowed=not reasons,
        reasons=tuple(reasons),
    )