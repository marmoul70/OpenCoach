"""Fake déterministe du fournisseur de séance.

Cette implémentation sert uniquement aux tests automatiques et aux
diagnostics sans fournisseur externe réel.

Elle respecte le même contrat que les futures implémentations
externes ou distantes.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.sessions.coach_port import (
    SessionCoachRequest,
)
from opencoach.planning.sessions.proposal import (
    SessionBlock,
    SessionProposal,
)
from opencoach.planning.stimulus.training import (
    TrainingModality,
)


@dataclass(frozen=True, slots=True)
class FakeSessionCoach:
    """Coach déterministe produisant une proposition simple."""

    default_duration_minutes: int = 60

    def __post_init__(self) -> None:
        if self.default_duration_minutes <= 0:
            raise ValueError(
                "La durée par défaut doit être "
                "strictement positive."
            )

    def generate_session(
        self,
        *,
        request: SessionCoachRequest,
    ) -> SessionProposal:
        """Produit une séance déterministe à partir du slot."""

        intent = request.slot.intent

        duration = _resolve_duration(
            request=request,
            default_duration_minutes=(
                self.default_duration_minutes
            ),
        )

        modality = _resolve_modality(
            request=request,
        )

        return SessionProposal(
            title=_build_title(
                request=request,
            ),
            modality=modality,
            duration_minutes=duration,
            covered_stimuli=(
                intent.stimuli
            ),
            blocks=(
                SessionBlock(
                    name="Séance",
                    description=(
                        "Séance déterministe générée "
                        "par FakeSessionCoach."
                    ),
                    duration_minutes=duration,
                ),
            ),
            objective=_build_objective(
                request=request,
            ),
            coach_notes=(
                "Proposition générée par le fake OpenCoach.",
            ),
        )


def _resolve_duration(
    *,
    request: SessionCoachRequest,
    default_duration_minutes: int,
) -> int:
    intent = request.slot.intent

    minimum = intent.duration_min_minutes

    maximum = intent.duration_max_minutes

    available = (
        request.slot.duration_available_minutes
    )

    if minimum is not None:
        duration = minimum
    else:
        duration = default_duration_minutes

    if maximum is not None:
        duration = min(
            duration,
            maximum,
        )

    if available is not None:
        duration = min(
            duration,
            available,
        )

    if (
        minimum is not None
        and duration < minimum
    ):
        raise ValueError(
            "La capacité temporelle du créneau est "
            "incompatible avec la durée minimale de l'intention."
        )

    return duration


def _resolve_modality(
    *,
    request: SessionCoachRequest,
) -> TrainingModality:
    intent = request.slot.intent

    if intent.required_modalities:
        return intent.required_modalities[0]

    if intent.preferred_modalities:
        return intent.preferred_modalities[0]

    return TrainingModality.RUNNING


def _build_title(
    *,
    request: SessionCoachRequest,
) -> str:
    stimulus = (
        request.slot
        .intent
        .primary_stimulus
        .value
        .replace("_", " ")
    )

    return stimulus.capitalize()


def _build_objective(
    *,
    request: SessionCoachRequest,
) -> str:
    stimuli = ", ".join(
        stimulus.value
        for stimulus
        in request.slot.intent.stimuli
    )

    return (
        "Développer les stimuli suivants : "
        f"{stimuli}."
    )
