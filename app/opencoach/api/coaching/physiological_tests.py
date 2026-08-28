"""API des propositions de tests physiologiques OpenCoach.

Le coach peut proposer un test afin de recalibrer certaines
métriques physiologiques.

L'athlète conserve toujours la décision finale :

- accepter :
    la séance qualitative ciblée devient une séance de test ;

- refuser :
    la séance qualitative initialement prévue reste inchangée.

Cette API ne réalise aucune analyse physiologique.
L'analyse de l'activité synchronisée sera prise en charge
ultérieurement par le moteur général d'analyse des séances.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.database.repositories.physiological_test_proposal import (
    PhysiologicalTestProposalRepository,
    PhysiologicalTestProposalRepositoryError,
)
from opencoach.physiology.testing.protocol_details import (
    get_physiological_test_protocol_details,
)

from opencoach.physiology.testing import (
    ApplyPhysiologicalTestDecisionService,
    PhysiologicalMetric,
    PhysiologicalTestApplicationError,
    PhysiologicalTestApplicationResult,
    PhysiologicalTestApplicationStatus,
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
    PhysiologicalTestReplacementStimulus,
    PhysiologicalTestType,
)

from .dependencies import (
    get_physiological_test_application_service,
    get_physiological_test_proposal_repository,
)


router = APIRouter(
    prefix="/api/coach/physiological-tests",
    tags=[
        "coach-physiological-tests",
    ],
)




class PhysiologicalTestStepResponse(
    BaseModel
):
    title: str
    description: str
    duration_minutes: int | None


class PhysiologicalTestProtocolDetailsResponse(
    BaseModel
):
    protocol: str

    title: str
    short_description: str

    target_metrics: list[str]

    total_duration_minutes: int

    terrain_recommendation: str

    preparation: list[str]

    warmup: list[
        PhysiologicalTestStepResponse
    ]

    test_steps: list[
        PhysiologicalTestStepResponse
    ]

    cooldown: list[
        PhysiologicalTestStepResponse
    ]

    execution_advice: list[str]

    invalidation_reasons: list[str]

    required_activity_data: list[str]

    useful_activity_data: list[str]

    analysis_notes: list[str]


class PhysiologicalTestProposalResponse(
    BaseModel
):
    """Proposition de test exposée à l'athlète."""

    id: UUID

    protocol: PhysiologicalTestType

    target_metrics: list[
        PhysiologicalMetric
    ]

    proposed_date: date

    reason: str
    recommendation: str

    replacement_stimulus: (
        PhysiologicalTestReplacementStimulus
    )

    target_session_id: UUID | None

    decision: PhysiologicalTestDecision


class PhysiologicalTestSessionResponse(
    BaseModel
):
    """Séance résultant de l'application du test."""

    id: UUID

    date: date

    type: str
    sport_type: str

    title: str
    description: str

    duration_minutes: int

    planning_key: str | None

    distance_km: float | None
    elevation_gain_m: float | None

    intensity: str

    heart_rate_zone: str | None

    status: str

    activity_id: UUID | None


class PhysiologicalTestDecisionResponse(
    BaseModel
):
    """Résultat d'une décision de l'athlète."""

    proposal: PhysiologicalTestProposalResponse

    application_status: (
        PhysiologicalTestApplicationStatus
    )

    changed: bool

    session: (
        PhysiologicalTestSessionResponse
        | None
    )

    message: str


def _proposal_response(
    proposal: PhysiologicalTestProposal,
) -> PhysiologicalTestProposalResponse:
    """Convertit le domaine vers l'API."""

    if proposal.id is None:
        raise RuntimeError(
            "Une proposition exposée par l'API "
            "doit être persistée."
        )

    return PhysiologicalTestProposalResponse(
        id=proposal.id,
        protocol=proposal.protocol,
        target_metrics=list(
            proposal.target_metrics
        ),
        proposed_date=(
            proposal.proposed_date
        ),
        reason=proposal.reason,
        recommendation=(
            proposal.recommendation
        ),
        replacement_stimulus=(
            proposal.replacement_stimulus
        ),
        target_session_id=(
            proposal.target_session_id
        ),
        decision=proposal.decision,
    )


def _session_response(
    result: PhysiologicalTestApplicationResult,
) -> PhysiologicalTestSessionResponse | None:
    """Convertit la séance résultante vers l'API."""

    session = (
        result.resulting_session
    )

    if session is None:
        return None

    if session.id is None:
        raise RuntimeError(
            "Une séance persistée doit "
            "posséder un identifiant."
        )

    return PhysiologicalTestSessionResponse(
        id=session.id,
        date=session.date,
        type=session.type,
        sport_type=session.sport_type,
        title=session.title,
        description=session.description,
        duration_minutes=(
            session.duration_minutes
        ),
        planning_key=(
            session.planning_key
        ),
        distance_km=(
            session.distance_km
        ),
        elevation_gain_m=(
            session.elevation_gain_m
        ),
        intensity=session.intensity,
        heart_rate_zone=(
            session.heart_rate_zone
        ),
        status=session.status,
        activity_id=(
            session.activity_id
        ),
    )


def _load_proposal(
    *,
    athlete_profile_id: UUID,
    proposal_id: UUID,
    repository: PhysiologicalTestProposalRepository,
) -> PhysiologicalTestProposal:
    """Charge une proposition appartenant à l'athlète."""

    try:
        proposal = repository.get(
            athlete_profile_id,
            proposal_id,
        )

    except (
        PhysiologicalTestProposalRepositoryError
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger "
                "la proposition de test."
            ),
        ) from exc

    if proposal is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Proposition de test introuvable."
            ),
        )

    return proposal




@router.get(
    "/protocols/{protocol}",
    response_model=(
        PhysiologicalTestProtocolDetailsResponse
    ),
)
def get_physiological_test_protocol(
    protocol: str,
) -> PhysiologicalTestProtocolDetailsResponse:
    """Retourne les consignes détaillées d'un test physiologique."""

    try:
        protocol_type = (
            PhysiologicalTestType(
                protocol
            )
        )

        details = (
            get_physiological_test_protocol_details(
                protocol_type
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Protocole de test "
                "physiologique introuvable."
            ),
        ) from exc

    def step_response(
        step,
    ) -> PhysiologicalTestStepResponse:
        return (
            PhysiologicalTestStepResponse(
                title=step.title,
                description=(
                    step.description
                ),
                duration_minutes=(
                    step.duration_minutes
                ),
            )
        )

    return (
        PhysiologicalTestProtocolDetailsResponse(
            protocol=(
                details.protocol.value
            ),
            title=details.title,
            short_description=(
                details.short_description
            ),
            target_metrics=[
                metric.value
                for metric
                in details.target_metrics
            ],
            total_duration_minutes=(
                details.total_duration_minutes
            ),
            terrain_recommendation=(
                details.terrain_recommendation
            ),
            preparation=list(
                details.preparation
            ),
            warmup=[
                step_response(step)
                for step
                in details.warmup
            ],
            test_steps=[
                step_response(step)
                for step
                in details.test_steps
            ],
            cooldown=[
                step_response(step)
                for step
                in details.cooldown
            ],
            execution_advice=list(
                details.execution_advice
            ),
            invalidation_reasons=list(
                details.invalidation_reasons
            ),
            required_activity_data=list(
                details.required_activity_data
            ),
            useful_activity_data=list(
                details.useful_activity_data
            ),
            analysis_notes=list(
                details.analysis_notes
            ),
        )
    )


@router.get(
    "/pending",
    response_model=list[
        PhysiologicalTestProposalResponse
    ],
)
def list_pending_physiological_tests(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id
    ),
    repository: PhysiologicalTestProposalRepository = Depends(
        get_physiological_test_proposal_repository
    ),
) -> list[
    PhysiologicalTestProposalResponse
]:
    """Retourne les tests attendant une décision."""

    try:
        proposals = repository.get_pending(
            athlete_profile_id
        )

    except (
        PhysiologicalTestProposalRepositoryError
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger "
                "les tests proposés."
            ),
        ) from exc

    return [
        _proposal_response(
            proposal
        )
        for proposal
        in proposals
    ]


@router.post(
    "/{proposal_id}/accept",
    response_model=(
        PhysiologicalTestDecisionResponse
    ),
)
def accept_physiological_test(
    proposal_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id
    ),
    repository: PhysiologicalTestProposalRepository = Depends(
        get_physiological_test_proposal_repository
    ),
    application_service: ApplyPhysiologicalTestDecisionService = Depends(
        get_physiological_test_application_service
    ),
) -> PhysiologicalTestDecisionResponse:
    """Accepte un test et l'applique à la séance ciblée."""

    proposal = _load_proposal(
        athlete_profile_id=(
            athlete_profile_id
        ),
        proposal_id=proposal_id,
        repository=repository,
    )

    if (
        proposal.decision
        is PhysiologicalTestDecision.DECLINED
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cette proposition de test "
                "a déjà été refusée."
            ),
        )

    accepted = (
        proposal.accept()
    )

    try:
        application = (
            application_service.apply(
                proposal=accepted,
            )
        )

    except (
        PhysiologicalTestApplicationError
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                exc
            ),
        ) from exc

    try:
        saved = repository.save(
            accepted
        )

    except (
        PhysiologicalTestProposalRepositoryError
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Le test a été appliqué mais "
                "la décision n'a pas pu être "
                "enregistrée."
            ),
        ) from exc

    return (
        PhysiologicalTestDecisionResponse(
            proposal=(
                _proposal_response(
                    saved
                )
            ),
            application_status=(
                application.status
            ),
            changed=(
                application.changed
            ),
            session=(
                _session_response(
                    application
                )
            ),
            message=(
                application.reason
            ),
        )
    )


@router.post(
    "/{proposal_id}/decline",
    response_model=(
        PhysiologicalTestDecisionResponse
    ),
)
def decline_physiological_test(
    proposal_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id
    ),
    repository: PhysiologicalTestProposalRepository = Depends(
        get_physiological_test_proposal_repository
    ),
    application_service: ApplyPhysiologicalTestDecisionService = Depends(
        get_physiological_test_application_service
    ),
) -> PhysiologicalTestDecisionResponse:
    """Refuse un test et conserve la séance qualitative."""

    proposal = _load_proposal(
        athlete_profile_id=(
            athlete_profile_id
        ),
        proposal_id=proposal_id,
        repository=repository,
    )

    if (
        proposal.decision
        is PhysiologicalTestDecision.ACCEPTED
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Cette proposition de test "
                "a déjà été acceptée."
            ),
        )

    declined = (
        proposal.decline()
    )

    application = (
        application_service.apply(
            proposal=declined,
        )
    )

    try:
        saved = repository.save(
            declined
        )

    except (
        PhysiologicalTestProposalRepositoryError
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible d'enregistrer "
                "le refus du test."
            ),
        ) from exc

    return (
        PhysiologicalTestDecisionResponse(
            proposal=(
                _proposal_response(
                    saved
                )
            ),
            application_status=(
                application.status
            ),
            changed=(
                application.changed
            ),
            session=(
                _session_response(
                    application
                )
            ),
            message=(
                application.reason
            ),
        )
    )
