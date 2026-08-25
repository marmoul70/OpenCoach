from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.session import get_db


router = APIRouter(
    prefix="/api/health",
    tags=["health"],
)


@router.get("")
def health() -> dict[str, str]:
    """Confirme que le processus FastAPI répond."""

    return {
        "status": "healthy",
    }


@router.get("/ready")
def readiness(
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Vérifie que l'application peut accéder à sa base."""

    try:
        db.execute(
            text("SELECT 1")
        ).scalar_one()

    except SQLAlchemyError:
        return JSONResponse(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            content={
                "status": "unhealthy",
                "database": "unhealthy",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "database": "healthy",
        },
    )
