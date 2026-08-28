"""Construction déterministe des propositions de test physiologique."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.physiology.testing.catalog import (
    get_test_protocol,
)
from opencoach.physiology.testing.models import (
    PhysiologicalTestType,
)
from opencoach.physiology.testing.proposal import (
    PhysiologicalTestProposal,
)
from opencoach.physiology.testing.replacement import (
    get_test_replacement_stimulus,
)


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestProposalRequest:
    """Informations nécessaires pour proposer un test."""

    athlete_profile_id: UUID

    protocol: PhysiologicalTestType

    proposed_date: date

    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(
                "La raison de la proposition "
                "ne peut pas être vide."
            )


def propose_physiological_test(
    request: PhysiologicalTestProposalRequest,
) -> PhysiologicalTestProposal:
    """Construit une proposition sans modifier le planning.

    Cette fonction ne programme aucune séance.

    Elle décrit seulement :
    - pourquoi OpenCoach recommande le test ;
    - quel protocole est proposé ;
    - quelles métriques seront recalibrées ;
    - quel stimulus devra remplacer le test si l'athlète refuse.
    """

    protocol = get_test_protocol(
        request.protocol
    )

    recommendation = (
        f"OpenCoach recommande le test "
        f"« {protocol.name} ». "
        "Cette évaluation permettra de mettre "
        "à jour les données utilisées pour calibrer "
        "les prochaines séances. "
        "Le test reste facultatif."
    )

    return PhysiologicalTestProposal(
        athlete_profile_id=(
            request.athlete_profile_id
        ),
        protocol=request.protocol,
        target_metrics=(
            protocol.target_metrics
        ),
        proposed_date=(
            request.proposed_date
        ),
        reason=request.reason,
        recommendation=recommendation,
        replacement_stimulus=(
            get_test_replacement_stimulus(
                request.protocol
            )
        ),
    )
