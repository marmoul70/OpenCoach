"""Application d'une décision de test physiologique au planning.

Ce module constitue la frontière entre :
- la proposition abstraite de test ;
- la séance TrainingSession réellement persistée.

Invariant principal :
un test accepté remplace le contenu d'une séance existante
sans changer son identifiant ni augmenter le nombre de séances.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    TrainingSession,
)
from opencoach.physiology.testing.proposal import (
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
)
from opencoach.physiology.testing.session import (
    PhysiologicalTestSession,
)
from opencoach.physiology.testing.session_generator import (
    generate_physiological_test_session,
)


class PhysiologicalTestApplicationStatus(StrEnum):
    """Résultat de l'application au planning."""

    AWAITING_ATHLETE = "awaiting_athlete"
    DECLINED = "declined"
    APPLIED = "applied"
    ALREADY_APPLIED = "already_applied"


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestApplicationResult:
    """Résultat explicable de l'application."""

    status: PhysiologicalTestApplicationStatus

    proposal: PhysiologicalTestProposal

    original_session: (
        TrainingSession
        | None
    )

    resulting_session: (
        TrainingSession
        | None
    )

    reason: str

    @property
    def changed(
        self,
    ) -> bool:
        return (
            self.status
            is PhysiologicalTestApplicationStatus.APPLIED
        )


class PhysiologicalTestApplicationError(
    RuntimeError
):
    """Impossible d'appliquer le test au planning."""


class ApplyPhysiologicalTestDecisionService:
    """Applique une décision de test à une séance existante."""

    def __init__(
        self,
        *,
        training_session_repository: (
            TrainingSessionRepository
        ),
    ) -> None:
        self.training_session_repository = (
            training_session_repository
        )

    def apply(
        self,
        *,
        proposal: PhysiologicalTestProposal,
    ) -> PhysiologicalTestApplicationResult:
        """Applique la décision sans créer de nouvelle séance."""

        # ----------------------------------------------------
        # L'athlète n'a pas encore répondu
        # ----------------------------------------------------

        if (
            proposal.decision
            is PhysiologicalTestDecision.PENDING
        ):
            return (
                PhysiologicalTestApplicationResult(
                    status=(
                        PhysiologicalTestApplicationStatus
                        .AWAITING_ATHLETE
                    ),
                    proposal=proposal,
                    original_session=None,
                    resulting_session=None,
                    reason=(
                        "OpenCoach attend encore "
                        "la décision de l'athlète."
                    ),
                )
            )

        # ----------------------------------------------------
        # Refus :
        # la séance qualitative existante reste intacte
        # ----------------------------------------------------

        if (
            proposal.decision
            is PhysiologicalTestDecision.DECLINED
        ):
            return (
                PhysiologicalTestApplicationResult(
                    status=(
                        PhysiologicalTestApplicationStatus
                        .DECLINED
                    ),
                    proposal=proposal,
                    original_session=None,
                    resulting_session=None,
                    reason=(
                        "Le test a été refusé. "
                        "La séance qualitative initiale "
                        "reste au programme."
                    ),
                )
            )

        # ----------------------------------------------------
        # Acceptation :
        # une vraie séance cible est obligatoire
        # ----------------------------------------------------

        if proposal.target_session_id is None:
            raise PhysiologicalTestApplicationError(
                "La proposition acceptée n'est rattachée "
                "à aucune séance du planning."
            )

        session = (
            self.training_session_repository
            .get_session(
                proposal.athlete_profile_id,
                proposal.target_session_id,
            )
        )

        if session is None:
            raise PhysiologicalTestApplicationError(
                "La séance ciblée par le test "
                "est introuvable."
            )

        # ----------------------------------------------------
        # Une activité déjà réalisée est immuable
        # ----------------------------------------------------

        if session.activity_id is not None:
            raise PhysiologicalTestApplicationError(
                "Une séance déjà liée à une activité "
                "ne peut pas être remplacée par un test."
            )

        # ----------------------------------------------------
        # Idempotence
        # ----------------------------------------------------

        expected_planning_key = (
            _test_planning_key(
                proposal
            )
        )

        if (
            session.type
            == "physiological_test"
            and session.planning_key
            == expected_planning_key
        ):
            return (
                PhysiologicalTestApplicationResult(
                    status=(
                        PhysiologicalTestApplicationStatus
                        .ALREADY_APPLIED
                    ),
                    proposal=proposal,
                    original_session=session,
                    resulting_session=session,
                    reason=(
                        "Ce test est déjà appliqué "
                        "à la séance ciblée."
                    ),
                )
            )

        if session.status != "planned":
            raise PhysiologicalTestApplicationError(
                "Seule une séance encore planifiée "
                "peut être remplacée par un test."
            )

        generated = (
            generate_physiological_test_session(
                proposal.protocol
            )
        )

        replacement = (
            _replace_training_session_with_test(
                original=session,
                generated=generated,
            )
        )

        saved = (
            self.training_session_repository
            .save_session(
                proposal.athlete_profile_id,
                replacement,
            )
        )

        if saved.id != session.id:
            raise PhysiologicalTestApplicationError(
                "Le remplacement d'un test ne doit jamais "
                "créer une nouvelle séance."
            )

        return PhysiologicalTestApplicationResult(
            status=(
                PhysiologicalTestApplicationStatus
                .APPLIED
            ),
            proposal=proposal,
            original_session=session,
            resulting_session=saved,
            reason=(
                "Le test accepté remplace la séance "
                "qualitative ciblée sans modifier "
                "son identifiant."
            ),
        )


def _replace_training_session_with_test(
    *,
    original: TrainingSession,
    generated: PhysiologicalTestSession,
) -> TrainingSession:
    """Transforme une séance existante en séance de test."""

    return TrainingSession(
        id=original.id,
        date=original.date,
        type="physiological_test",
        sport_type=original.sport_type,
        title=generated.title,
        description=(
            _build_test_description(
                generated
            )
        ),
        duration_minutes=(
            generated
            .expected_total_duration_minutes
        ),
        planning_key=(
            "physiological_test:"
            f"{generated.protocol.value}"
        ),
        distance_km=None,
        elevation_gain_m=None,
        intensity="hard",
        heart_rate_zone=None,
        status="planned",
        activity_id=None,
    )


def _build_test_description(
    session: PhysiologicalTestSession,
) -> str:
    """Produit une description lisible pour le planning."""

    lines = [
        session.description,
        "",
        "Déroulement :",
    ]

    for segment in session.segments:
        lines.append(
            f"- {segment.title} : "
            f"{segment.instruction}"
        )

    if session.terrain_requirements:
        lines.extend(
            [
                "",
                "Terrain :",
            ]
        )

        lines.extend(
            f"- {requirement}"
            for requirement
            in session.terrain_requirements
        )

    return "\n".join(
        lines
    )


def _test_planning_key(
    proposal: PhysiologicalTestProposal,
) -> str:
    """Identifiant stable utilisé dans TrainingSession."""

    return (
        "physiological_test:"
        f"{proposal.protocol.value}"
    )
