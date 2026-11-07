"""Endpoints de diagnostic du moteur IA local optionnel."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from opencoach.ai.config import AISettings, get_ai_settings
from opencoach.authentication.dependencies import get_current_user_id

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AIStatusResponse(BaseModel):
    """État de configuration non sensible du moteur IA."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    provider: str
    model: str
    provider_check: str


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status(
    _user_id=Depends(get_current_user_id),
    settings: AISettings = Depends(get_ai_settings),
) -> AIStatusResponse:
    """Expose l'activation IA sans contacter Ollama ni révéler son URL."""
    return AIStatusResponse(
        enabled=settings.enabled,
        provider=settings.provider,
        model=settings.model,
        provider_check="not_checked",
    )
