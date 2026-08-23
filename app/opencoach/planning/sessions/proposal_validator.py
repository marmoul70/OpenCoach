"""Validation déterministe des propositions de séance.

Un fournisseur peut produire une SessionProposal concrète, mais le moteur
Python reste l'autorité sur les contraintes structurelles.

Ce module vérifie notamment :
- la durée ;
- la capacité temporelle du créneau ;
- les modalités imposées ;
- les stimuli que l'intention doit couvrir.

La validation ne juge pas la qualité éditoriale ou sportive fine
de la séance. Elle vérifie uniquement sa conformité au contrat
déterministe OpenCoach.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.planning.sessions.coach_port import (
    SessionCoachRequest,
)
from opencoach.planning.sessions.proposal import (
    SessionProposal,
)


class SessionProposalViolation(StrEnum):
    """Type de violation détectée dans une proposition de séance."""

    DURATION_BELOW_MINIMUM = "duration_below_minimum"

    DURATION_ABOVE_MAXIMUM = "duration_above_maximum"

    DURATION_ABOVE_AVAILABILITY = (
        "duration_above_availability"
    )

    REQUIRED_MODALITY_NOT_RESPECTED = (
        "required_modality_not_respected"
    )

    PRIMARY_STIMULUS_MISSING = (
        "primary_stimulus_missing"
    )

    SECONDARY_STIMULUS_MISSING = (
        "secondary_stimulus_missing"
    )


@dataclass(frozen=True, slots=True)
class SessionProposalValidationIssue:
    """Violation précise d'une proposition de séance."""

    violation: SessionProposalViolation

    message: str

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError(
                "Le message d'une violation ne peut pas être vide."
            )


@dataclass(frozen=True, slots=True)
class SessionProposalValidationResult:
    """Résultat complet de validation d'une proposition de séance."""

    valid: bool

    issues: tuple[
        SessionProposalValidationIssue,
        ...
    ]

    def __post_init__(self) -> None:
        if (
            self.valid
            and self.issues
        ):
            raise ValueError(
                "Une validation valide ne peut pas contenir "
                "de violations."
            )

        if (
            not self.valid
            and not self.issues
        ):
            raise ValueError(
                "Une validation invalide doit contenir "
                "au moins une violation."
            )

    @property
    def violations(
        self,
    ) -> tuple[
        SessionProposalViolation,
        ...
    ]:
        """Retourne uniquement les types de violations."""

        return tuple(
            issue.violation
            for issue in self.issues
        )


def validate_session_proposal(
    *,
    request: SessionCoachRequest,
    proposal: SessionProposal,
) -> SessionProposalValidationResult:
    """Vérifie qu'une proposition respecte l'intention Python."""

    issues: list[
        SessionProposalValidationIssue
    ] = []

    _validate_duration(
        request=request,
        proposal=proposal,
        issues=issues,
    )

    _validate_modality(
        request=request,
        proposal=proposal,
        issues=issues,
    )

    _validate_stimuli(
        request=request,
        proposal=proposal,
        issues=issues,
    )

    if not issues:
        return SessionProposalValidationResult(
            valid=True,
            issues=(),
        )

    return SessionProposalValidationResult(
        valid=False,
        issues=tuple(
            issues
        ),
    )


def _validate_duration(
    *,
    request: SessionCoachRequest,
    proposal: SessionProposal,
    issues: list[
        SessionProposalValidationIssue
    ],
) -> None:
    intent = request.slot.intent

    minimum = (
        intent.duration_min_minutes
    )

    maximum = (
        intent.duration_max_minutes
    )

    available = (
        request.slot.duration_available_minutes
    )

    if (
        minimum is not None
        and proposal.duration_minutes < minimum
    ):
        issues.append(
            SessionProposalValidationIssue(
                violation=(
                    SessionProposalViolation
                    .DURATION_BELOW_MINIMUM
                ),
                message=(
                    "La durée proposée "
                    f"({proposal.duration_minutes} min) "
                    "est inférieure à la durée minimale "
                    f"de l'intention ({minimum} min)."
                ),
            )
        )

    if (
        maximum is not None
        and proposal.duration_minutes > maximum
    ):
        issues.append(
            SessionProposalValidationIssue(
                violation=(
                    SessionProposalViolation
                    .DURATION_ABOVE_MAXIMUM
                ),
                message=(
                    "La durée proposée "
                    f"({proposal.duration_minutes} min) "
                    "dépasse la durée maximale "
                    f"de l'intention ({maximum} min)."
                ),
            )
        )

    if (
        available is not None
        and proposal.duration_minutes > available
    ):
        issues.append(
            SessionProposalValidationIssue(
                violation=(
                    SessionProposalViolation
                    .DURATION_ABOVE_AVAILABILITY
                ),
                message=(
                    "La durée proposée "
                    f"({proposal.duration_minutes} min) "
                    "dépasse le temps disponible "
                    f"({available} min)."
                ),
            )
        )


def _validate_modality(
    *,
    request: SessionCoachRequest,
    proposal: SessionProposal,
    issues: list[
        SessionProposalValidationIssue
    ],
) -> None:
    required_modalities = (
        request.slot.intent.required_modalities
    )

    if not required_modalities:
        return

    if proposal.modality in required_modalities:
        return

    expected = ", ".join(
        modality.value
        for modality
        in required_modalities
    )

    issues.append(
        SessionProposalValidationIssue(
            violation=(
                SessionProposalViolation
                .REQUIRED_MODALITY_NOT_RESPECTED
            ),
            message=(
                "La modalité proposée "
                f"'{proposal.modality.value}' "
                "ne respecte pas les modalités obligatoires : "
                f"{expected}."
            ),
        )
    )


def _validate_stimuli(
    *,
    request: SessionCoachRequest,
    proposal: SessionProposal,
    issues: list[
        SessionProposalValidationIssue
    ],
) -> None:
    intent = request.slot.intent

    covered = set(
        proposal.covered_stimuli
    )

    if (
        intent.primary_stimulus
        not in covered
    ):
        issues.append(
            SessionProposalValidationIssue(
                violation=(
                    SessionProposalViolation
                    .PRIMARY_STIMULUS_MISSING
                ),
                message=(
                    "Le stimulus principal "
                    f"'{intent.primary_stimulus.value}' "
                    "n'est pas couvert par la séance proposée."
                ),
            )
        )

    for stimulus in (
        intent.secondary_stimuli
    ):
        if stimulus in covered:
            continue

        issues.append(
            SessionProposalValidationIssue(
                violation=(
                    SessionProposalViolation
                    .SECONDARY_STIMULUS_MISSING
                ),
                message=(
                    "Le stimulus secondaire "
                    f"'{stimulus.value}' "
                    "n'est pas couvert par la séance proposée."
                ),
            )
        )
