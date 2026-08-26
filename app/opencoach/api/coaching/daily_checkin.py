"""API du check-in quotidien de l'athlète.

Cette API expose l'état subjectif quotidien de l'athlète et
les propositions d'adaptation du coach.

Une proposition acceptée autorise une adaptation ultérieure,
mais cet endpoint ne modifie pas encore directement une séance.
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
from pydantic import (
    BaseModel,
    Field,
)

from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)
from opencoach.coaching.daily_adaptation_application import (
    ApplyAcceptedDailyAdaptationService,
    DailyAdaptationApplicationError,
    DailyAdaptationSessionAmbiguousError,
    DailyAdaptationSessionNotFoundError,
)
from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
    BodySide,
    PainArea,
    PainLocation,
)
from opencoach.coaching.daily_checkin_policy import (
    assess_daily_checkin,
)
from opencoach.coaching.daily_adaptation_service import (
    build_daily_adaptation_proposal,
)
from opencoach.database.repositories.daily_adaptation import (
    DailyAdaptationRepository,
)
from opencoach.database.repositories.daily_checkin import (
    DailyCheckInRepository,
)
from opencoach.database.repositories.sql_training_session import (
    SqlTrainingSessionRepository,
)

from .dependencies import (
    get_daily_adaptation_repository,
    get_daily_checkin_repository,
    get_training_session_repository,
)


router = APIRouter(
    prefix="/api/coach/check-in",
    tags=["coach-check-in"],
)


class PainLocationPayload(BaseModel):
    """Localisation d'une douleur déclarée."""

    area: PainArea

    side: BodySide = (
        BodySide.NOT_APPLICABLE
    )


class DailyCheckInPayload(BaseModel):
    """Données saisies par l'athlète."""

    energy_rating: int = Field(
        ge=1,
        le=5,
    )

    pain_wellness_rating: int = Field(
        ge=1,
        le=5,
    )

    illness: bool = False
    unavailable: bool = False

    pain_locations: tuple[
        PainLocationPayload,
        ...
    ] = ()

    note: str | None = Field(
        default=None,
        max_length=1000,
    )


class PainLocationResponse(BaseModel):
    """Localisation exposée par l'API."""

    area: PainArea
    side: BodySide


class DailyCheckInResponse(BaseModel):
    """Check-in quotidien exposé par l'API."""

    id: UUID
    date: date

    energy_rating: int
    pain_wellness_rating: int

    illness: bool
    unavailable: bool

    pain_locations: tuple[
        PainLocationResponse,
        ...
    ]

    note: str | None


class AdaptationProposalResponse(BaseModel):
    """Proposition du coach exposée au frontend."""

    id: UUID
    checkin_id: UUID

    reason: str
    recommendation: str
    decision: str

    awaiting_athlete_decision: bool
    adaptation_authorized: bool


class DailyCheckInStateResponse(BaseModel):
    """État complet du dialogue quotidien."""

    checkin: DailyCheckInResponse

    adaptation: (
        AdaptationProposalResponse
        | None
    ) = None


def _checkin_response(
    checkin: AthleteDailyCheckIn,
) -> DailyCheckInResponse:
    if checkin.id is None:
        raise RuntimeError(
            "Un check-in persisté doit posséder un identifiant."
        )

    return DailyCheckInResponse(
        id=checkin.id,
        date=checkin.date,
        energy_rating=(
            checkin.energy_rating
        ),
        pain_wellness_rating=(
            checkin.pain_wellness_rating
        ),
        illness=checkin.illness,
        unavailable=checkin.unavailable,
        pain_locations=tuple(
            PainLocationResponse(
                area=location.area,
                side=location.side,
            )
            for location
            in checkin.pain_locations
        ),
        note=checkin.note,
    )


def _adaptation_response(
    proposal: CoachAdaptationProposal,
) -> AdaptationProposalResponse:
    if proposal.id is None:
        raise RuntimeError(
            "Une proposition persistée doit posséder "
            "un identifiant."
        )

    return AdaptationProposalResponse(
        id=proposal.id,
        checkin_id=proposal.checkin_id,
        reason=proposal.reason,
        recommendation=(
            proposal.recommendation
        ),
        decision=proposal.decision.value,
        awaiting_athlete_decision=(
            proposal.awaiting_athlete_decision
        ),
        adaptation_authorized=(
            proposal.adaptation_authorized
        ),
    )


def _state_response(
    *,
    checkin: AthleteDailyCheckIn,
    proposal: (
        CoachAdaptationProposal
        | None
    ),
) -> DailyCheckInStateResponse:
    return DailyCheckInStateResponse(
        checkin=_checkin_response(
            checkin
        ),
        adaptation=(
            _adaptation_response(
                proposal
            )
            if proposal is not None
            else None
        ),
    )


@router.post(
    "",
    response_model=DailyCheckInStateResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_daily_checkin(
    payload: DailyCheckInPayload,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id
    ),
    checkin_repository: DailyCheckInRepository = Depends(
        get_daily_checkin_repository
    ),
    adaptation_repository: DailyAdaptationRepository = Depends(
        get_daily_adaptation_repository
    ),
) -> DailyCheckInStateResponse:
    """Crée ou actualise le check-in du jour."""

    try:
        checkin = AthleteDailyCheckIn(
            date=date.today(),
            energy_rating=(
                payload.energy_rating
            ),
            pain_wellness_rating=(
                payload.pain_wellness_rating
            ),
            illness=payload.illness,
            unavailable=(
                payload.unavailable
            ),
            pain_locations=tuple(
                PainLocation(
                    area=location.area,
                    side=location.side,
                )
                for location
                in payload.pain_locations
            ),
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    saved = checkin_repository.save(
        athlete_profile_id,
        checkin,
    )

    if saved.id is None:
        raise RuntimeError(
            "Le repository n'a pas attribué "
            "d'identifiant au check-in."
        )

    assessment = assess_daily_checkin(
        saved
    )

    generated_proposal = (
        build_daily_adaptation_proposal(
            checkin_id=saved.id,
            assessment=assessment,
        )
    )

    existing_proposal = (
        adaptation_repository
        .get_for_checkin(
            athlete_profile_id,
            saved.id,
        )
    )

    if (
        generated_proposal is not None
        and existing_proposal is None
    ):
        proposal = (
            adaptation_repository.save(
                athlete_profile_id,
                generated_proposal,
            )
        )

    elif (
        generated_proposal is not None
        and existing_proposal is not None
        and existing_proposal.awaiting_athlete_decision
    ):
        proposal = (
            adaptation_repository.save(
                athlete_profile_id,
                CoachAdaptationProposal(
                    id=existing_proposal.id,
                    checkin_id=saved.id,
                    reason=generated_proposal.reason,
                    recommendation=(
                        generated_proposal.recommendation
                    ),
                    decision=(
                        existing_proposal.decision
                    ),
                ),
            )
        )

    elif (
        generated_proposal is None
        and existing_proposal is not None
        and existing_proposal.awaiting_athlete_decision
    ):
        adaptation_repository.delete_for_checkin(
            athlete_profile_id,
            saved.id,
        )

        proposal = None

    else:
        proposal = existing_proposal

    return _state_response(
        checkin=saved,
        proposal=proposal,
    )


@router.get(
    "/today",
    response_model=DailyCheckInStateResponse,
)
def get_today_daily_checkin(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id
    ),
    checkin_repository: DailyCheckInRepository = Depends(
        get_daily_checkin_repository
    ),
    adaptation_repository: DailyAdaptationRepository = Depends(
        get_daily_adaptation_repository
    ),
) -> DailyCheckInStateResponse:
    """Retourne le dialogue quotidien du jour."""

    checkin = (
        checkin_repository.get_for_date(
            athlete_profile_id,
            date.today(),
        )
    )

    if checkin is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Aucun check-in pour aujourd'hui."
            ),
        )

    if checkin.id is None:
        raise RuntimeError(
            "Le check-in chargé ne possède "
            "pas d'identifiant."
        )

    proposal = (
        adaptation_repository
        .get_for_checkin(
            athlete_profile_id,
            checkin.id,
        )
    )

    return _state_response(
        checkin=checkin,
        proposal=proposal,
    )


def _change_adaptation_decision(
    *,
    checkin_id: UUID,
    athlete_profile_id: UUID,
    adaptation_repository: (
        DailyAdaptationRepository
    ),
    accept: bool,
) -> AdaptationProposalResponse:
    proposal = (
        adaptation_repository
        .get_for_checkin(
            athlete_profile_id,
            checkin_id,
        )
    )

    if proposal is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Aucune proposition d'adaptation "
                "pour ce check-in."
            ),
        )

    updated = (
        proposal.accept()
        if accept
        else proposal.decline()
    )

    saved = adaptation_repository.save(
        athlete_profile_id,
        updated,
    )

    return _adaptation_response(
        saved
    )


@router.post(
    "/{checkin_id}/adaptation/accept",
    response_model=AdaptationProposalResponse,
)
@router.post(
    "/{checkin_id}/adaptation/accept",
)
def accept_daily_adaptation(
    checkin_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id
    ),
    checkin_repository: DailyCheckInRepository = Depends(
        get_daily_checkin_repository
    ),
    adaptation_repository: DailyAdaptationRepository = Depends(
        get_daily_adaptation_repository
    ),
    training_session_repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository
    ),
):
    """Accepte et applique l'adaptation de la séance du jour."""

    checkin = checkin_repository.get_for_date(
        athlete_profile_id,
        date.today(),
    )

    if (
        checkin is None
        or checkin.id != checkin_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Check-in introuvable.",
        )

    proposal = (
        adaptation_repository
        .get_for_checkin(
            athlete_profile_id,
            checkin_id,
        )
    )

    if proposal is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Aucune proposition d'adaptation "
                "pour ce check-in."
            ),
        )

    # --------------------------------------------------------
    # Idempotence
    # --------------------------------------------------------

    if proposal.adaptation_authorized:
        return {
            "proposal": _adaptation_response(
                proposal
            ),
            "session_adapted": False,
            "already_accepted": True,
            "adapted_session": None,
            "reasons": [],
        }

    if not proposal.awaiting_athlete_decision:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cette proposition a déjà été refusée."
            ),
        )

    accepted = proposal.accept()

    service = (
        ApplyAcceptedDailyAdaptationService(
            training_session_repository=(
                training_session_repository
            )
        )
    )

    try:
        result = service.execute(
            athlete_profile_id=(
                athlete_profile_id
            ),
            checkin=checkin,
            proposal=accepted,
        )

    except DailyAdaptationSessionNotFoundError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except DailyAdaptationSessionAmbiguousError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except DailyAdaptationApplicationError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    saved_proposal = (
        adaptation_repository.save(
            athlete_profile_id,
            accepted,
        )
    )

    adapted_session = None

    if result.changed:
        adapted_session = {
            "id": (
                str(result.adapted.id)
                if result.adapted.id is not None
                else None
            ),
            "date": (
                result.adapted.date.isoformat()
            ),
            "type": (
                result.adapted.type
            ),
            "sport_type": (
                result.adapted.sport_type
            ),
            "title": (
                result.adapted.title
            ),
            "description": (
                result.adapted.description
            ),
            "duration_minutes": (
                result.adapted.duration_minutes
            ),
            "intensity": (
                result.adapted.intensity
            ),
            "heart_rate_zone": (
                result.adapted.heart_rate_zone
            ),
            "status": (
                result.adapted.status
            ),
        }

    return {
        "proposal": _adaptation_response(
            saved_proposal
        ),
        "session_adapted": (
            result.changed
        ),
        "already_accepted": False,
        "adapted_session": (
            adapted_session
        ),
        "reasons": list(
            result.reasons
        ),
    }



@router.post(
    "/{checkin_id}/adaptation/decline",
    response_model=AdaptationProposalResponse,
)
def decline_daily_adaptation(
    checkin_id: UUID,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id
    ),
    adaptation_repository: DailyAdaptationRepository = Depends(
        get_daily_adaptation_repository
    ),
) -> AdaptationProposalResponse:
    """Refuse l'adaptation et conserve la séance actuelle."""

    return _change_adaptation_decision(
        checkin_id=checkin_id,
        athlete_profile_id=(
            athlete_profile_id
        ),
        adaptation_repository=(
            adaptation_repository
        ),
        accept=False,
    )
