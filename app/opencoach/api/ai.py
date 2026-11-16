"""Endpoints authentifiés du moteur IA local optionnel."""

from __future__ import annotations

from time import perf_counter
from uuid import UUID
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from pydantic import ValidationError

from opencoach.ai.client import AIProviderError
from opencoach.ai.observability import (
    get_ai_metrics_snapshot,
    log_ai_event,
    new_ai_trace_id,
)
from opencoach.ai.data_collection_tools import build_profile_data_proposal_tool
from opencoach.coaching.profile_data_proposals import (
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
    AIStatusResponse,
    AIQuestionRequest,
    AIQuestionResponse,
    AIChatRequest,
    AIMessage,
    AICoachPreferencesPayload,
    AICoachPreferencesResponse,
)
from opencoach.ai.prompts import (
    _CHAT_SYSTEM_PROMPT,
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
from opencoach.ai.response_synthesis import (
    _coach_generation_failure_answer,
    _coach_planned_session_fallback_answer,
    _coach_provider_unavailable_answer,
    _coach_response_has_ungrounded_risk_claims,
    _coach_response_needs_rewrite,
    _coach_response_quality_fallback_answer,
    _coach_running_restriction_answer,
    _extract_coach_analysis_periods,
    _extract_race_options,
    _serialize_coach_tool_results,
    _trim_coach_payload,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])

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
