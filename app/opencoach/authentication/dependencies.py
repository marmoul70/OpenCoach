"""Dépendances FastAPI liées à l'utilisateur authentifié."""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    Depends,
    HTTPException,
    Request,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import (
    AthleteProfile,
)
from opencoach.database.session import (
    get_db,
)


def get_current_user_id(
    request: Request,
) -> UUID:
    """Retourne l'UUID de l'utilisateur authentifié.

    L'identité est injectée dans ``request.state`` par
    ``AuthenticationMiddleware`` après validation du cookie
    de session OpenCoach.
    """

    raw_user_id = getattr(
        request.state,
        "user_id",
        None,
    )

    if not raw_user_id:
        raise HTTPException(
            status_code=401,
            detail=(
                "Session utilisateur invalide."
            ),
        )

    try:
        return UUID(
            str(
                raw_user_id
            )
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=401,
            detail=(
                "Session utilisateur invalide."
            ),
        ) from exc


def get_current_athlete_profile_id(
    user_id: UUID = Depends(
        get_current_user_id,
    ),
    db: Session = Depends(
        get_db,
    ),
) -> UUID:
    """Retourne le profil de l'utilisateur authentifié."""

    profile_id = db.scalar(
        select(
            AthleteProfile.id
        )
        .where(
            AthleteProfile.user_id
            == user_id
        )
    )

    if profile_id is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Profil athlète introuvable "
                "pour cet utilisateur."
            ),
        )

    return profile_id

