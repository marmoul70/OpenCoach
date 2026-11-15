"""Synthèse, garde-fous et sérialisation des résultats des outils IA."""

from __future__ import annotations

import json
import re
from datetime import date

from opencoach.ai.schemas import AIRaceOptionResponse


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
