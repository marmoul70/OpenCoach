"""Endpoints authentifiés du moteur IA local optionnel."""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.client import AIProviderError
from opencoach.ai.config import AISettings, get_ai_settings
from opencoach.ai.schemas import AIChatRequest, AIMessage
from opencoach.ai.service import AIService, AIServiceDisabledError
from opencoach.authentication.dependencies import get_current_user_id

router = APIRouter(prefix="/api/ai", tags=["ai"])

_SYSTEM_PROMPT = """Tu es l'assistant local d'OpenCoach.
Réponds en français, de façon claire, prudente et concise.
Tu n'as accès à aucune donnée personnelle ou activité sportive dans cette conversation,
sauf si elles sont explicitement fournies dans la question.
N'invente jamais de mesure, d'activité, de disponibilité COROS ou de recommandation
présentée comme issue du dossier de l'athlète.
Tu ne peux ni modifier un entraînement, ni créer une séance, ni écrire dans COROS.
Pour toute décision d'entraînement individualisée, indique que les données athlète
doivent d'abord être chargées par les services déterministes OpenCoach.
Ne prétends jamais avoir exécuté une action ou consulté une source que tu n'as pas reçue."""


class AIStatusResponse(BaseModel):
    """État de configuration non sensible du moteur IA."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    provider: str
    model: str
    provider_check: str


class AIQuestionRequest(BaseModel):
    """Question utilisateur ; aucun rôle système n'est accepté."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question: str = Field(min_length=1, max_length=4_000)


class AIQuestionResponse(BaseModel):
    """Réponse générée par le modèle local."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answer: str
    model: str


@lru_cache(maxsize=8)
def _cached_ai_service(settings: AISettings) -> AIService:
    """Partage le limiteur de concurrence entre requêtes API."""
    return AIService(settings)


def get_ai_service(
    settings: AISettings = Depends(get_ai_settings),
) -> AIService:
    return _cached_ai_service(settings)


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


@router.post("/chat", response_model=AIQuestionResponse)
async def ask_local_ai(
    payload: AIQuestionRequest,
    _user_id=Depends(get_current_user_id),
    service: AIService = Depends(get_ai_service),
) -> AIQuestionResponse:
    """Dialogue local contrôlé, sans accès direct aux données métier."""
    request = AIChatRequest(
        messages=[
            AIMessage(role="system", content=_SYSTEM_PROMPT),
            AIMessage(role="user", content=payload.question.strip()),
        ],
        temperature=0.2,
        num_predict=512,
    )
    try:
        result = await service.chat(request)
    except AIServiceDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le moteur IA local est désactivé.",
        ) from exc
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return AIQuestionResponse(
        answer=result.content,
        model=result.model,
    )
