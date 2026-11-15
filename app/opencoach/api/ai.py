"""Endpoints authentifiés du moteur IA local optionnel."""

from __future__ import annotations

import json
import re
from time import perf_counter
from uuid import UUID
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from opencoach.ai.client import AIProviderError
from opencoach.ai.observability import (
    get_ai_metrics_snapshot,
    log_ai_event,
    new_ai_trace_id,
)
from opencoach.ai.data_collection_tools import build_profile_data_proposal_tool
from opencoach.ai.data_proposals import (
    AIDataProposalCreate,
    AIDataProposalResponse,
    confirm_profile_data_proposal,
    create_profile_data_proposal,
    get_profile_data_proposal,
    list_pending_profile_data_proposals,
    reject_profile_data_proposal,
)
from opencoach.ai.config import AISettings, get_ai_settings
from opencoach.ai.schemas import (
    AIChatRequest,
    AIMessage,
    AICoachPreferencesPayload,
    AICoachPreferencesResponse,
)
from opencoach.ai.prompts import (
    _CHAT_SYSTEM_PROMPT,
    _COACH_SYSTEM_PROMPT,
    _coach_response_token_budget,
    _coach_synthesis_system_prompt,
    _coach_system_prompt,
)
from opencoach.ai.service import AIService, AIServiceDisabledError
from opencoach.ai.tool_engine import AIToolRegistry
from opencoach.ai.execution_plan import build_coach_execution_plan
from opencoach.database.session import get_db
from opencoach.api.training_stats import get_training_stats_service
from opencoach.training import TrainingStatsService
from opencoach.database.models.ai_coach_preference import AICoachPreference
from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
    get_current_user_id,
)
from opencoach.api.coaching.dependencies import get_planning_context_service
from opencoach.planning.service import PlanningContextService
from opencoach.ai.registry import build_ai_tool_registry

router = APIRouter(prefix="/api/ai", tags=["ai"])

class AIStatusResponse(BaseModel):
    """État de configuration non sensible du moteur IA."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    provider: str
    model: str
    provider_check: str


class AIConversationMessage(BaseModel):
    """Message d'historique client, limité aux rôles conversationnels."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4_000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Le contenu d'un message ne peut pas être vide.")
        return normalized


class AIQuestionRequest(BaseModel):
    """Question et historique borné ; aucun rôle système n'est accepté."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question: str = Field(min_length=1, max_length=4_000)
    history: list[AIConversationMessage] = Field(default_factory=list, max_length=8)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("La question ne peut pas être vide.")
        return normalized

    @model_validator(mode="after")
    def validate_history_size(self):
        total_chars = sum(len(message.content) for message in self.history)
        if total_chars > 12_000:
            raise ValueError("L'historique dépasse la taille autorisée.")
        return self


class AIRaceOptionResponse(BaseModel):
    """Course du calendrier proposée pour une sélection explicite."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    race_id: UUID
    date: str
    name: str
    location: str | None = None
    race_type: str | None = None
    priority: str | None = None
    status: str | None = None
    distance_km: float | None = None
    elevation_gain_m: float | None = None
    target_time_minutes: float | None = None


def _extract_coach_analysis_periods(tool_results) -> list[dict[str, str | int]]:
    """Expose uniquement les fenêtres datées explicitement retournées par les outils."""
    periods: list[dict[str, str | int]] = []
    seen: set[tuple[str, str]] = set()
    label_by_path = {
        "current_period": "période récente",
        "comparison_period": "période précédente",
        "baseline_period": "période de référence",
        "windows": "fenêtre analysée",
        "week": "semaine analysée",
        "period": "période analysée",
    }

    def visit(tool: str, value, path: str = "") -> None:
        if isinstance(value, dict):
            start = value.get("start_date")
            end = value.get("end_date")
            if isinstance(start, str) and isinstance(end, str):
                key = (start, end)
                if key not in seen:
                    path_key = path.split()[-1] if path else "period"
                    item: dict[str, str | int] = {
                        "tool": tool,
                        "label": label_by_path.get(path_key, "période analysée"),
                        "start_date": start,
                        "end_date": end,
                    }
                    for duration_key in ("nb_days", "days", "horizon_days"):
                        duration = value.get(duration_key)
                        if isinstance(duration, int) and not isinstance(duration, bool) and duration > 0:
                            item["days"] = duration
                            break
                    periods.append(item)
                    seen.add(key)
            for key, child in value.items():
                if isinstance(child, (dict, list)):
                    visit(tool, child, f"{path} {key}".strip())
        elif isinstance(value, list):
            for child in value:
                if isinstance(child, (dict, list)):
                    visit(tool, child, path)

    for result in tool_results:
        if result.status == "ok" and isinstance(result.data, dict):
            visit(result.tool, result.data)
    return periods


class AIQuestionResponse(BaseModel):
    """Réponse générée par le modèle local."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answer: str
    model: str
    context_used: bool = False
    data_proposals: list[AIDataProposalResponse] = Field(default_factory=list)
    race_options: list[AIRaceOptionResponse] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    analysis_periods: list[dict[str, str | int]] = Field(default_factory=list)



_DEFAULT_COACH_PREFERENCES = AICoachPreferencesPayload()


def _preferences_response(
    preferences: AICoachPreference | None,
) -> AICoachPreferencesResponse:
    if preferences is None:
        return AICoachPreferencesResponse(**_DEFAULT_COACH_PREFERENCES.model_dump())
    return AICoachPreferencesResponse(
        personality=preferences.personality,
        firmness=preferences.firmness,
        motivation=preferences.motivation,
        response_style=preferences.response_style,
        custom_prompt=preferences.custom_prompt,
    )


@router.get("/preferences", response_model=AICoachPreferencesResponse)
def get_ai_coach_preferences(
    user_id=Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> AICoachPreferencesResponse:
    preferences = db.scalar(
        select(AICoachPreference).where(AICoachPreference.user_id == user_id)
    )
    return _preferences_response(preferences)


@router.put("/preferences", response_model=AICoachPreferencesResponse)
def save_ai_coach_preferences(
    payload: AICoachPreferencesPayload,
    user_id=Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> AICoachPreferencesResponse:
    preferences = db.scalar(
        select(AICoachPreference).where(AICoachPreference.user_id == user_id)
    )
    values = payload.model_dump()
    if preferences is None:
        preferences = AICoachPreference(user_id=user_id, **values)
        db.add(preferences)
    else:
        for key, value in values.items():
            setattr(preferences, key, value)
    db.commit()
    db.refresh(preferences)
    return _preferences_response(preferences)


@router.post("/preferences/reset", response_model=AICoachPreferencesResponse)
def reset_ai_coach_preferences(
    user_id=Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> AICoachPreferencesResponse:
    preferences = db.scalar(
        select(AICoachPreference).where(AICoachPreference.user_id == user_id)
    )
    if preferences is not None:
        db.delete(preferences)
        db.commit()
    return _preferences_response(None)

@lru_cache(maxsize=8)
def _cached_ai_service(settings: AISettings) -> AIService:
    """Partage le limiteur de concurrence entre requêtes API."""
    return AIService(settings)


def get_ai_service(
    settings: AISettings = Depends(get_ai_settings),
) -> AIService:
    return _cached_ai_service(settings)


def get_ai_tool_registry(
    db: Session = Depends(get_db),
    athlete_profile_id=Depends(get_current_athlete_profile_id),
    training_stats_service: TrainingStatsService = Depends(
        get_training_stats_service,
    ),
    context_service: PlanningContextService = Depends(get_planning_context_service),
) -> AIToolRegistry:
    """Construit le registre IA depuis les dépendances authentifiées."""
    return build_ai_tool_registry(
        db=db,
        athlete_profile_id=athlete_profile_id,
        training_stats_service=training_stats_service,
        context_service=context_service,
    )


def _proposal_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, TimeoutError):
        return HTTPException(status_code=410, detail=str(exc))
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=422, detail="La proposition viole les règles de cohérence du profil.")
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Impossible de traiter la proposition de donnée.")


@router.post("/data-proposals", response_model=AIDataProposalResponse, status_code=201)
def propose_profile_data_update(
    payload: AIDataProposalCreate,
    athlete_profile_id=Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> AIDataProposalResponse:
    """Crée une proposition en attente ; ne modifie jamais le profil."""
    try:
        return create_profile_data_proposal(db, athlete_profile_id, payload)
    except Exception as exc:
        raise _proposal_http_error(exc) from exc


@router.get("/data-proposals", response_model=list[AIDataProposalResponse])
def list_profile_data_proposals(
    athlete_profile_id=Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> list[AIDataProposalResponse]:
    return list_pending_profile_data_proposals(db, athlete_profile_id)


@router.get("/data-proposals/{proposal_id}", response_model=AIDataProposalResponse)
def read_profile_data_proposal(
    proposal_id: UUID,
    athlete_profile_id=Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> AIDataProposalResponse:
    try:
        return get_profile_data_proposal(db, athlete_profile_id, proposal_id)
    except Exception as exc:
        raise _proposal_http_error(exc) from exc


@router.post(
    "/data-proposals/{proposal_id}/confirm",
    response_model=AIDataProposalResponse,
)
def confirm_profile_data_update(
    proposal_id: UUID,
    athlete_profile_id=Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> AIDataProposalResponse:
    """Applique une proposition après action explicite sur cet endpoint."""
    try:
        return confirm_profile_data_proposal(db, athlete_profile_id, proposal_id)
    except Exception as exc:
        raise _proposal_http_error(exc) from exc


@router.post(
    "/data-proposals/{proposal_id}/reject",
    response_model=AIDataProposalResponse,
)
def reject_profile_data_update(
    proposal_id: UUID,
    athlete_profile_id=Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> AIDataProposalResponse:
    try:
        return reject_profile_data_proposal(db, athlete_profile_id, proposal_id)
    except Exception as exc:
        raise _proposal_http_error(exc) from exc


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


@router.post("/chat", response_model=AIQuestionResponse, response_model_exclude_defaults=True)
async def ask_local_ai(
    payload: AIQuestionRequest,
    _user_id=Depends(get_current_user_id),
    service: AIService = Depends(get_ai_service),
) -> AIQuestionResponse:
    """Dialogue local contrôlé, sans accès direct aux données métier."""
    trace_id = new_ai_trace_id()
    request = AIChatRequest(
        trace_id=trace_id,
        messages=[
            AIMessage(role="system", content=_CHAT_SYSTEM_PROMPT),
            *[
                AIMessage(role=message.role, content=message.content)
                for message in payload.history
            ],
            AIMessage(role="user", content=payload.question),
        ],
        temperature=0.2,
        num_predict=512,
    )
    try:
        generation_started_at = perf_counter()
        result = await service.chat(request)
        log_ai_event(
            "coach_generation",
            trace_id=trace_id,
            status="ok" if result.done and result.done_reason != "length" and result.content.strip() else "truncated",
            model=result.model,
            operation="initial_generation",
            duration_ms=round((perf_counter() - generation_started_at) * 1000, 3),
        )
        if not result.done or result.done_reason == "length" or not result.content.strip():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Le moteur IA a interrompu la génération avant la fin de la réponse.",
            )
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


def _extract_race_options(tool_results) -> list[AIRaceOptionResponse]:
    """Expose les courses du calendrier au frontend sans laisser le LLM les reconstruire."""
    options: list[AIRaceOptionResponse] = []
    for result in tool_results:
        if result.tool != "race_calendar" or result.status != "ok" or not result.data:
            continue
        races = result.data.get("races")
        if not isinstance(races, list):
            continue
        for race in races:
            if not isinstance(race, dict):
                continue
            try:
                options.append(AIRaceOptionResponse.model_validate({
                    "race_id": race.get("race_id"),
                    "date": race.get("date"),
                    "name": race.get("name") or "Course sans nom",
                    "location": race.get("location"),
                    "race_type": race.get("race_type"),
                    "priority": race.get("priority"),
                    "status": race.get("status"),
                    "distance_km": race.get("distance_km"),
                    "elevation_gain_m": race.get("elevation_gain_m"),
                    "target_time_minutes": race.get("target_time_minutes"),
                }))
            except ValidationError:
                # Une entrée mal formée ne doit pas empêcher l'affichage des autres courses.
                continue
    return options


_EXPLICIT_COACH_DATA_REQUEST = re.compile(
    r"\b(?:combien|chiffres?|statistiques?|tableau|liste(?:-moi)?|"
    r"d[eé]tail(?:le|l|s)? les donn[eé]es|valeurs exactes|"
    r"donne(?:-moi)? les (?:distances|dur[eé]es|donn[eé]es|m[eé]triques)|"
    r"r[eé]capitulatif chiffr[eé])\b",
    re.IGNORECASE,
)
_COACH_OPENING_JUDGMENT = re.compile(
    r"\b(?:mon avis|je te conseille|je recommande|je privilégie|"
    r"ta semaine (?:est|reste|semble|montre|a été)|"
    r"la semaine (?:est|reste|semble|a été)|cette semaine (?:est|reste|semble|a été)|"
    r"ton entraînement (?:est|reste|semble)|la charge (?:est|reste|semble)|"
    r"ta charge (?:est|reste|semble)|la récupération (?:est|reste|semble)|"
    r"ta récupération (?:est|reste|semble)|"
    r"je (?:garderais|maintiendrais|réduirais|remplacerais|reporterais|"
    r"partirais|privilégierais|te conseille|te propose|partirais sur)|"
    r"(?:aujourd'hui|pour aujourd'hui|pour ta prochaine séance),? "
    r"(?:je |tu peux |privilégie |pars sur |opte pour )|"
    r"la séance (?:du jour|d'aujourd'hui|idéale)|"
    r"tu peux (?:maintenir|alléger|réduire|remplacer|reporter)|"
    r"tu as (?:bien|correctement|difficilement|mal) "
    r"(?:géré|absorbé|encaissé|récupéré|enchaîné|respecté|toléré)|"
    r"globalement,? (?:ta|ton) |à ta place,? je |"
    r"il vaut mieux|le point (?:positif|de vigilance)|"
    r"c'est (?:une semaine|cohérent|adapté|trop))\b",
    re.IGNORECASE,
)
_COACH_UNIT_CLAIM = re.compile(
    r"(?<![\w])\d+(?:[.,]\d+)?\s*(?:km/h|km|m\b|heures?|h\b|"
    r"minutes?|min\b|bpm|%|jours?|semaines?)",
    re.IGNORECASE,
)
_COACH_BULLET_LINE = re.compile(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+")
_COACH_STRUCTURED_DATA = re.compile(
    r"""(?:\{\s*["']?[a-z_]+["']?\s*:|["'][a-z_]+["']?\s*:\s*(?:\d|["'{]))""",
    re.IGNORECASE,
)


_COACH_ACTIONABLE_GUIDANCE = re.compile(
    r"\\b(?:je te conseille|je recommande|je propose|je privilégie|"
    r"tu peux|tu devrais|il vaut mieux|"
    r"garde|maintiens|réduis|allège|remplace|reporte|"
    r"pars sur|opte pour|privilégie|évite|"
    r"séance facile|endurance fondamentale|récupération active|"
    r"repos|footing|fractionné|renforcement)\\b",
    re.IGNORECASE,
)


def _coach_response_needs_rewrite(question: str, answer: str) -> bool:
    """Rejette les tableaux de bord, pas les formulations naturelles du coach."""
    if _EXPLICIT_COACH_DATA_REQUEST.search(question):
        return False

    content = answer.strip()
    if not content:
        return True

    # Les défauts réellement bloquants sont structurels : inventaire ou données brutes.
    if _COACH_BULLET_LINE.search(content) or _COACH_STRUCTURED_DATA.search(content):
        return True

    unit_claims = len(_COACH_UNIT_CLAIM.findall(content))
    has_actionable_guidance = bool(_COACH_ACTIONABLE_GUIDANCE.search(content))
    first_sentence = re.split(r"(?<=[.!?])\\s+", content, maxsplit=1)[0]
    has_coach_opening = bool(_COACH_OPENING_JUDGMENT.search(first_sentence))

    # Une recommandation concrète peut être formulée après une phrase de contexte.
    # Le seuil numérique ne s'applique qu'aux réponses qui restent descriptives.
    if unit_claims > 2 and not has_actionable_guidance:
        return True
    return not (has_coach_opening or has_actionable_guidance)

def _coach_response_has_ungrounded_risk_claims(answer: str, tool_results) -> bool:
    """Rejects risky health/load claims that lack explicit structured evidence."""
    content = answer.casefold()
    results = {
        item.tool: item.data
        for item in tool_results
        if item.status == "ok" and isinstance(item.data, dict)
    }

    # A single 7-day window is not a trend. Current-vs-average is not a
    # comparable before/after measurement, so directional fatigue claims fail.
    if re.search(
        r"\bfatigue\b.{0,70}\b(?:en baisse|en hausse|diminue|augmente|"
        r"s'aggrave|s'améliore|a diminué|a augmenté)\b",
        content,
    ):
        recovery = results.get("recovery_analysis") or {}
        if not isinstance(recovery.get("trend"), dict):
            return True

    # A stress alert must be an explicit Readiness signal, not a model's
    # interpretation of a raw stress score.
    if re.search(
        r"\bstress\b.{0,70}\b(?:en alerte|alerte|inqui[eé]tant|critique|alarmant)\b",
        content,
    ):
        recovery_status = results.get("recovery_status") or {}
        signals = recovery_status.get("signals", [])
        supported = any(
            isinstance(signal, dict)
            and "stress" in str(signal.get("metric", "")).casefold()
            and str(signal.get("level", "")).casefold()
                in {"warning", "critical", "alert", "high"}
            for signal in signals
        )
        if not supported:
            return True

    # The load service deliberately exposes no low/high classification or
    # individual threshold. The model must not invent one.
    if re.search(
        r"\b(?:charge|charge de travail|charge d'entraînement)\b"
        r".{0,45}\b(?:basse|faible|élevée|haute|excessive|maîtrisée)\b",
        content,
    ):
        load = results.get("training_load") or {}
        if not load.get("classification"):
            return True

    # Do not cancel a planned session unless a dated OpenCoach constraint
    # explicitly prohibits it. Generic stress/fatigue wording is insufficient.
    if re.search(
        r"\b(?:ne pas|pas)\s+(?:faire|prendre|effectuer|maintenir)\s+"
        r"(?:cette\s+|la\s+)?(?:prochaine\s+)?s[eé]ance\b|"
        r"\bannul(?:er|e)\s+(?:cette\s+|la\s+)?s[eé]ance\b|"
        r"\bne pas reprendre\b",
        content,
    ):
        constraints_data = results.get("active_constraints") or {}
        constraints = constraints_data.get("constraints", [])
        explicitly_blocked = any(
            isinstance(item, dict) and item.get("running_allowed") is False
            for item in constraints
        )
        if not explicitly_blocked:
            return True

    # A profile is complete only when the tool reports status=ok and no missing fields.
    if re.search(
        r"\bprofil\b.{0,55}\b(?:correctement|compl[eè]tement|parfaitement)\s+"
        r"(?:d[eé]fini|renseign[eé]|configur[eé])\b",
        content,
    ):
        profile = results.get("athlete_training_profile") or {}
        if profile.get("status") != "ok" or profile.get("missing_profile_fields"):
            return True

    return False


def _coach_running_restriction_answer(question: str, tool_results) -> str | None:
    """Bloque une recommandation de course quand une contrainte métier l'interdit.

    Cette règle Python est indépendante de la rédaction Ollama et utilise
    exclusivement running_allowed / cross_training_allowed issus d'OpenCoach.
    """
    if not re.search(
        r"\b(?:s[eé]ance|entra[iî]n\w*|courir|course|footing|sortie|"
        r"que faire|dois-je faire|conseill\w*|recommand\w*|adapt\w*|ajust\w*)\b",
        question,
        re.IGNORECASE,
    ):
        return None

    constraints = [
        constraint
        for item in tool_results
        if item.tool == "active_constraints" and item.status == "ok"
        for constraint in (item.data or {}).get("constraints", [])
        if isinstance(constraint, dict)
    ]
    if not any(constraint.get("running_allowed") is False for constraint in constraints):
        return None

    cross_training_allowed = all(
        constraint.get("cross_training_allowed") is True
        for constraint in constraints
    )
    answer = (
        "La restriction enregistrée dans OpenCoach interdit actuellement "
        "la course à pied pour la date concernée, même si ta Readiness est favorable. "
        "Je ne peux donc pas te conseiller de maintenir une séance en courant. "
    )
    if cross_training_allowed:
        answer += (
            "Une activité croisée peut être envisagée uniquement si elle reste "
            "indolore et respecte les autres limites enregistrées. "
        )
    else:
        answer += (
            "Je ne peux pas non plus te proposer une activité croisée sans "
            "autorisation explicite dans tes contraintes. "
        )
    return answer + (
        "Vérifie l'évolution de la douleur et fais réévaluer la restriction "
        "si nécessaire avant de reprendre la course."
    )


def _coach_planned_session_fallback_answer(question: str, tool_results) -> str | None:
    """Builds a minimal, grounded answer when LLM synthesis fails quality checks."""
    if not re.search(
        r"\b(?:quelle|que|qu[e']?est-ce que|dois-je|conseill\w*|recommand\w*)\b"
        r".{0,90}\b(?:s[eé]ance|entra[iî]n\w*|aujourd'hui|aujourd hui)\b",
        question,
        re.IGNORECASE,
    ):
        return None

    results = {
        item.tool: item.data
        for item in tool_results
        if item.status == "ok" and isinstance(item.data, dict)
    }
    planned = results.get("next_planned_session") or {}
    if planned.get("status") != "ok":
        return None
    session = planned.get("session")
    if not isinstance(session, dict):
        return None

    session_date = session.get("date")
    reference_date = planned.get("reference_date")
    if not session_date or not reference_date:
        return None

    duration = session.get("duration_minutes")
    title = session.get("title")
    sport = session.get("sport_type") or session.get("type")
    intensity = session.get("intensity")
    details = []
    if sport:
        details.append(str(sport))
    if title and title.casefold() != str(sport or "").casefold():
        details.append(str(title))
    description = " – ".join(details) if details else "séance planifiée"
    if duration:
        description += f" de {duration} minutes"
    if intensity:
        description += f", intensité prévue : {intensity}"

    if session_date == reference_date:
        return (
            f"Pour aujourd'hui, conserve la séance déjà inscrite dans ton planning : "
            f"{description}. Je ne te propose pas de la durcir ni de la supprimer "
            f"sans élément fiable qui le justifie. Si tu ressens une douleur, un "
            f"symptôme inhabituel ou une fatigue nettement différente de ton état "
            f"habituel, ne force pas et fais le point avant de partir."
        )
    return (
        f"La prochaine séance enregistrée dans ton planning est prévue le "
        f"{session_date} : {description}. Je n'ai pas de séance planifiée pour "
        f"aujourd'hui dans les données consultées ; je préfère ne pas en inventer une."
    )


def _coach_response_quality_fallback_answer() -> str:
    """Ne masque pas un échec de rédaction par un faux diagnostic de panne."""
    return (
        "J'ai récupéré les éléments utiles de ton dossier, mais je n'ai pas réussi "
        "à formuler une synthèse de coach suffisamment claire. Je préfère ne pas "
        "te renvoyer un inventaire de chiffres mal interprété. Reformule ta demande "
        "ou réessaie dans un instant."
    )


def _coach_provider_unavailable_answer() -> str:
    """Réponse de secours lisible : ne jamais exposer les payloads métier bruts."""
    return (
        "J'ai bien récupéré les éléments disponibles dans ton dossier OpenCoach, "
        "mais mon moteur de rédaction local est momentanément indisponible. "
        "Je préfère ne pas te présenter une succession de chiffres sans pouvoir "
        "les interpréter correctement. Réessaie dans quelques instants : je pourrai "
        "alors te donner un véritable bilan de coach et une conduite à tenir."
    )

def _coach_generation_failure_answer(
    error: AIProviderError,
    question: str = "",
    tool_results=(),
) -> str:
    """Privilégie une réponse métier déterministe si la rédaction LLM échoue."""
    if "interrompu la rédaction" in str(error):
        return (
            _coach_planned_session_fallback_answer(question, tool_results)
            or _coach_response_quality_fallback_answer()
        )
    return _coach_provider_unavailable_answer()


def _trim_coach_payload(value, *, max_chars: int):
    """Réduit récursivement un résultat en conservant sa structure et ses premières données."""
    marker = "… données complémentaires omises"

    def encode(item):
        return json.dumps(item, ensure_ascii=False, default=str)

    if len(encode(value)) <= max_chars:
        return value
    if isinstance(value, str):
        return value[:max(0, max_chars - len(marker))] + marker
    if isinstance(value, list):
        kept = []
        item_budget = max(128, (max_chars - 80) // max(1, min(len(value), 8)))
        for item in value:
            candidate_item = _trim_coach_payload(item, max_chars=item_budget)
            candidate = [*kept, candidate_item]
            if len(encode(candidate)) > max_chars - 80:
                break
            kept.append(candidate_item)
        if len(kept) < len(value):
            kept.append(marker)
        return kept
    if isinstance(value, dict):
        trimmed = {}
        for key, item in value.items():
            trimmed[key] = _trim_coach_payload(
                item,
                max_chars=max(256, max_chars // max(1, len(value))),
            )
            if len(encode(trimmed)) > max_chars:
                trimmed.pop(key, None)
                break
        if len(trimmed) < len(value):
            trimmed["_truncated"] = True
        return trimmed
    return value


def _serialize_coach_tool_results(tool_results, *, max_item_chars: int = 10_000, max_total_chars: int = 20_000) -> str:
    """Borne les résultats envoyés au LLM sans effacer tout le contexte utile."""
    payloads = [item.model_dump(mode="json") for item in tool_results]

    for payload in payloads:
        encoded = json.dumps(payload, ensure_ascii=False, default=str)
        if len(encoded) > max_item_chars:
            payload["data"] = _trim_coach_payload(
                payload.get("data"),
                max_chars=max(256, max_item_chars - 1_000),
            )

    serialized = json.dumps(payloads, ensure_ascii=False, default=str)
    if len(serialized) > max_total_chars:
        # Répartit le budget entre les résultats au lieu de supprimer toutes
        # les données dès qu'un seul outil fait dépasser le plafond global.
        per_item_budget = max(512, (max_total_chars - 2 * len(payloads)) // max(1, len(payloads)))
        compact = []
        for payload in payloads:
            item = dict(payload)
            item["data"] = _trim_coach_payload(
                item.get("data"),
                max_chars=per_item_budget,
            )
            compact.append(item)
        serialized = json.dumps(compact, ensure_ascii=False, default=str)

    if len(serialized) > max_total_chars:
        # Ultime garde-fou : préserver au minimum l'identité et le statut de
        # chaque outil, ainsi que ses métadonnées compactes.
        compact = [
            {
                "tool": item.get("tool"),
                "status": item.get("status"),
                "error": item.get("error"),
                "metadata": _trim_coach_payload(item.get("metadata", {}), max_chars=512),
                "data": _trim_coach_payload(item.get("data"), max_chars=256),
            }
            for item in payloads
        ]
        serialized = json.dumps(compact, ensure_ascii=False, default=str)
    return serialized

@router.post("/coach", response_model=AIQuestionResponse)
async def ask_local_ai_with_athlete_context(
    payload: AIQuestionRequest,
    user_id=Depends(get_current_user_id),
    db: Session = Depends(get_db),
    athlete_profile_id=Depends(get_current_athlete_profile_id),
    service: AIService = Depends(get_ai_service),
    settings: AISettings = Depends(get_ai_settings),
    training_stats_service: TrainingStatsService = Depends(get_training_stats_service),
    context_service: PlanningContextService = Depends(get_planning_context_service),
) -> AIQuestionResponse:
    """Coach piloté par Python : planification, exécution métier, puis rédaction IA."""
    if not settings.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le moteur IA local est désactivé.",
        )

    trace_id = new_ai_trace_id()
    conversation_messages = [
        *[
            AIMessage(role=message.role, content=message.content)
            for message in payload.history
        ],
        AIMessage(role="user", content=payload.question),
    ]
    user_messages = [
        message.content for message in conversation_messages if message.role == "user"
    ]
    assistant_messages = [
        message.content for message in conversation_messages if message.role == "assistant"
    ]

    router_started_at = perf_counter()
    plan = build_coach_execution_plan(
        payload.question,
        history=user_messages[:-1],
        assistant_history=assistant_messages,
    )
    log_ai_event(
        "coach_router",
        trace_id=trace_id,
        status="needs_clarification" if plan.clarification else "ok",
        operation="execution_plan",
        duration_ms=round((perf_counter() - router_started_at) * 1000, 3),
    )
    if plan.clarification:
        return AIQuestionResponse(
            answer=plan.clarification,
            model=settings.model,
            context_used=False,
        )

    tool_results = []
    if plan.calls:
        tool_registry = get_ai_tool_registry(
            db=db,
            athlete_profile_id=athlete_profile_id,
            training_stats_service=training_stats_service,
            context_service=context_service,
        )
        # La proposition de profil reste une écriture en attente, jamais une
        # modification directe. Le registre valide toujours preuve et schéma.
        tool_registry.register(
            build_profile_data_proposal_tool(
                proposal_creator=lambda payload: create_profile_data_proposal(
                    db,
                    athlete_profile_id,
                    payload,
                ),
                user_messages=user_messages,
            )
        )
        tool_registry.trace_id = trace_id
        tool_registry.restrict_to({call.name for call in plan.calls})

        for call in plan.calls:
            tool_started_at = perf_counter()
            result = await run_in_threadpool(
                tool_registry.execute,
                call.name,
                call.arguments,
                user_messages=user_messages,
                assistant_messages=assistant_messages,
            )
            log_ai_event(
                "coach_tool_execution",
                trace_id=trace_id,
                status=result.status,
                tool=call.name,
                operation="business_data_collection",
                duration_ms=round((perf_counter() - tool_started_at) * 1000, 3),
            )
            tool_results.append(result)
            if (
                call.name == "active_constraints" and result.status != "ok"
            ) or (
                call.name == "recovery_status"
                and any(item.name == "active_constraints" for item in plan.calls)
                and result.status != "ok"
            ):
                return AIQuestionResponse(
                    answer=(
                        "Je n'ai pas pu consulter les contraintes ou la récupération dans OpenCoach. "
                        "Je ne peux donc pas te recommander de séance sur cette base. "
                        "Réessaie après vérification de la disponibilité du service."
                    ),
                    model=settings.model,
                    context_used=False,
                )
            if result.status == "needs_clarification":
                return AIQuestionResponse(
                    answer=result.error or "Une précision est nécessaire avant cette analyse.",
                    model=settings.model,
                    context_used=False,
                )
            if result.status == "invalid_arguments":
                return AIQuestionResponse(
                    answer=(
                        result.error
                        or "Les paramètres de cette analyse sont incomplets. Précise ta demande."
                    ),
                    model=settings.model,
                    context_used=False,
                )

    failed_tools = [item for item in tool_results if item.status == "failed"]
    if failed_tools:
        failed_names = ", ".join(item.tool for item in failed_tools)
        successful_names = ", ".join(
            item.tool for item in tool_results if item.status == "ok"
        )
        answer = (
            f"L'analyse n'a pas pu être terminée : échec de {failed_names}. "
            "Les détails techniques sont consignés dans les journaux du backend. "
            "Aucune conclusion ne sera tirée à partir de résultats incomplets."
        )
        if successful_names:
            answer += f" Outils exécutés avec succès : {successful_names}."
        return AIQuestionResponse(
            answer=answer,
            model=settings.model,
            context_used=any(item.status == "ok" for item in tool_results),
        )

    # Les interdictions de course sont des contraintes métier, pas une
    # préférence rédactionnelle du LLM. Elles sont appliquées après la collecte
    # Python et avant toute génération Ollama.
    restricted_answer = _coach_running_restriction_answer(payload.question, tool_results)
    if restricted_answer is not None:
        return AIQuestionResponse(
            answer=restricted_answer,
            model=settings.model,
            context_used=True,
        )

    preferences = db.scalar(
        select(AICoachPreference).where(AICoachPreference.user_id == user_id)
    )
    coach_preferences = (
        AICoachPreferencesPayload(
            personality=preferences.personality,
            firmness=preferences.firmness,
            motivation=preferences.motivation,
            response_style=preferences.response_style,
            custom_prompt=preferences.custom_prompt,
        )
        if preferences is not None
        else _DEFAULT_COACH_PREFERENCES
    )

    if tool_results:
        serialized_results = _serialize_coach_tool_results(tool_results)
        system_prompt = (
            _coach_synthesis_system_prompt(coach_preferences)
            + "\n\nMODE DE RÉDACTION APRÈS EXÉCUTION PYTHON : "
            "les outils nécessaires ont déjà été sélectionnés et exécutés par OpenCoach. "
            "Tu ne dois pas choisir d'outil, inventer d'arguments ou prétendre en appeler un. "
            "Explique uniquement les résultats structurés fournis, leurs périodes, leur "
            "couverture et leurs limites. Si un résultat est vide, partiel ou indisponible, "
            "dis-le explicitement. Ne transforme jamais une donnée absente en zéro. "
            "Ne calcule un pourcentage que si le numérateur et le dénominateur portent sur "
            "la même métrique, la même période et le même périmètre. N'assimile jamais "
            "couverture du planning, réalisation des séances et couverture des mesures. "
            "Pour une comparaison produite par training_trends, présente séparément les deux périodes. "
            "Pour chaque métrique, ne présente un écart que si son propre champ "
            "metrics.<nom_de_métrique>.trend.status vaut complete ; si ce statut vaut "
            "insufficient_coverage, explique que cette métrique n'est pas comparable. "
            "Les statuts de couverture sont propres à chaque métrique : n'exige pas un "
            "statut global trend.status, qui n'existe pas dans le résultat. Ignore tout champ absent."
        )
        messages = [
            AIMessage(role="system", content=system_prompt),
            *conversation_messages,
            AIMessage(
                role="user",
                content=(
                    "RÉSULTATS STRUCTURÉS DES OUTILS PYTHON OPENCOACH "
                    "(seules sources factuelles de cette analyse) :\n"
                    + serialized_results
                ),
            ),
        ]
    else:
        # Les questions générales ne construisent aucun contexte sportif et
        # n'exécutent aucun outil métier.
        messages = [
            AIMessage(role="system", content=_CHAT_SYSTEM_PROMPT),
            *conversation_messages,
        ]

    response_style = coach_preferences.response_style if tool_results else "concise"
    request = AIChatRequest(
        messages=messages,
        temperature=0.2,
        num_predict=_coach_response_token_budget(response_style),
        trace_id=trace_id,
    )

    try:
        generation_started_at = perf_counter()
        result = await service.chat(request)
        initial_generation_ok = (
            result.done and result.done_reason != "length" and bool(result.content.strip())
        )
        log_ai_event(
            "coach_generation",
            trace_id=trace_id,
            status="ok" if initial_generation_ok else "truncated",
            model=result.model,
            operation="initial_generation",
            duration_ms=round((perf_counter() - generation_started_at) * 1000, 3),
        )
        if not initial_generation_ok:
            raise AIProviderError(
                "Le moteur IA a interrompu la rédaction avant la fin de la réponse."
            )
        answer = result.content
        model = result.model
        if tool_results:
            quality_gate_started_at = perf_counter()
            initial_rejected = (
                _coach_response_needs_rewrite(payload.question, answer)
                or _coach_response_has_ungrounded_risk_claims(answer, tool_results)
            )
            log_ai_event(
                "coach_quality_gate",
                trace_id=trace_id,
                status="rejected" if initial_rejected else "accepted",
                model=model,
                operation=(
                    "initial_rejected"
                    if initial_rejected
                    else "initial_accepted"
                ),
                duration_ms=round((perf_counter() - quality_gate_started_at) * 1000, 3),
            )
        else:
            initial_rejected = False
        if tool_results and initial_rejected:
            # Une seule tentative de correction : ne pas laisser passer un
            # tableau de bord textuel lorsque l'athlète demande un conseil.
            rewrite_request = request.model_copy(
                update={
                    "messages": [
                        *messages,
                        AIMessage(role="assistant", content=answer),
                        AIMessage(
                            role="user",
                            content=(
                                "Réécris entièrement ta réponse comme un entraîneur qui "
                                "s'adresse à son athlète. Commence par ton avis et ta décision, "
                                "explique uniquement les faits décisifs, en prose naturelle. "
                                "Supprime les puces, tableaux, JSON et inventaires de métriques. "
                                "N'ajoute aucun chiffre qui ne figure pas dans les résultats. "
                                "N'annonce aucune alerte, tendance de fatigue, classification de charge "
                                "ou annulation de séance sans champ explicite qui le prouve. "
                                "Si la question demande explicitement des données chiffrées, "
                                "réponds précisément à cette demande."
                            ),
                        ),
                    ],
                }
            )
            rewrite_started_at = perf_counter()
            try:
                rewritten = await service.chat(rewrite_request)
                log_ai_event(
                    "coach_generation",
                    trace_id=trace_id,
                    status="ok" if rewritten.done and rewritten.done_reason != "length" and rewritten.content.strip() else "truncated",
                    model=rewritten.model,
                    operation="quality_rewrite",
                    duration_ms=round((perf_counter() - rewrite_started_at) * 1000, 3),
                )
            except AIProviderError as exc:
                log_ai_event(
                    "coach_generation",
                    trace_id=trace_id,
                    status="error",
                    model=settings.model,
                    operation="quality_rewrite",
                    error_type=type(exc).__name__,
                    duration_ms=round((perf_counter() - rewrite_started_at) * 1000, 3),
                )
                rewritten = None
            rewrite_gate_started_at = perf_counter()
            rewrite_accepted = (
                rewritten is not None
                and rewritten.done
                and rewritten.done_reason != "length"
                and bool(rewritten.content.strip())
                and not _coach_response_needs_rewrite(payload.question, rewritten.content)
                and not _coach_response_has_ungrounded_risk_claims(
                    rewritten.content, tool_results
                )
            )
            log_ai_event(
                "coach_quality_gate",
                trace_id=trace_id,
                status="accepted" if rewrite_accepted else "rejected",
                model=rewritten.model if rewritten is not None else settings.model,
                operation=(
                    "rewrite_accepted"
                    if rewrite_accepted
                    else "rewrite_rejected"
                ),
                duration_ms=round((perf_counter() - rewrite_gate_started_at) * 1000, 3),
            )
            if rewrite_accepted:
                answer = rewritten.content
                model = rewritten.model
            else:
                answer = (
                    _coach_planned_session_fallback_answer(payload.question, tool_results)
                    or _coach_response_quality_fallback_answer()
                )
    except AIProviderError as exc:
        if not tool_results:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
        # Les calculs Python ont déjà été exécutés : une panne du LLM ne doit
        # pas masquer les données ni faire échouer toute la consultation.
        answer = _coach_generation_failure_answer(exc, payload.question, tool_results)
        model = settings.model

    data_proposals = [
        AIDataProposalResponse(
            id=UUID(item.data["proposal_id"]),
            field_key=item.data["field_key"],
            value=item.data["value"],
            existing_value=item.data["existing_value"],
            unit=item.data["unit"],
            status=item.data["status"],
            expires_at=item.data["expires_at"],
        )
        for item in tool_results
        if item.tool == "propose_profile_data"
        and item.status == "ok"
        and item.data is not None
    ]

    if data_proposals:
        proposal = data_proposals[0]
        field_labels = {
            "vma": "VMA",
            "weight_kg": "poids",
            "height_cm": "taille",
            "max_heart_rate": "fréquence cardiaque maximale",
            "resting_heart_rate": "fréquence cardiaque au repos",
            "threshold_heart_rate_1": "fréquence cardiaque au seuil SV1",
            "threshold_heart_rate_2": "fréquence cardiaque au seuil SV2",
        }
        label = field_labels.get(proposal.field_key, proposal.field_key.replace("_", " "))
        value = f"{proposal.value} {proposal.unit}".strip()
        answer = (
            f"Je te propose d'enregistrer {label} à {value}. "
            "La proposition est en attente de ta confirmation dans OpenCoach ; "
            "ton profil n'a pas encore été modifié."
        )
        if proposal.existing_value is not None:
            answer += f" Valeur actuellement enregistrée : {proposal.existing_value} {proposal.unit}."

    return AIQuestionResponse(
        answer=answer,
        model=model,
        context_used=bool(tool_results),
        data_proposals=data_proposals,
        race_options=_extract_race_options(tool_results),
        tools_used=[item.tool for item in tool_results if item.status == "ok"],
        analysis_periods=_extract_coach_analysis_periods(tool_results),
    )



@router.get("/observability")
def get_ai_observability(
    window_hours: int = Query(default=24, ge=1, le=168),
    _user_id=Depends(get_current_user_id),
) -> dict:
    """Expose des agrégats techniques sans prompt ni donnée sportive."""
    return get_ai_metrics_snapshot(window_hours)
