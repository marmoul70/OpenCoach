"""Planification déterministe des outils du coach.

Le modèle ne choisit plus les outils et ne construit plus leurs arguments.
Ce module transforme les intentions explicites en appels validés par le registre Python.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from opencoach.ai.argument_evidence import (
    extract_explicit_date_range,
    extract_explicit_periods,
)
from opencoach.ai.tool_routing import select_coach_tools


@dataclass(frozen=True, slots=True)
class PlannedToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class CoachExecutionPlan:
    calls: tuple[PlannedToolCall, ...] = ()
    clarification: str | None = None


_MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def extract_activity_date(value: str, reference_date: date | None = None) -> date | None:
    """Extrait une date d'activité explicite ; ne devine jamais un jour absent."""
    reference_date = reference_date or date.today()
    normalized = _normalize(value)

    if "aujourd'hui" in normalized or "aujourd hui" in normalized:
        return reference_date
    if re.search(r"\bdemain\b", normalized):
        return reference_date + timedelta(days=1)
    if re.search(r"\bavant-hier\b", normalized):
        return reference_date - timedelta(days=2)
    if re.search(r"\bhier\b", normalized):
        return reference_date - timedelta(days=1)

    iso = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", normalized)
    if iso:
        try:
            return date.fromisoformat(iso.group(1))
        except ValueError:
            return None

    numeric = re.search(r"\b(?:le|du)\s+(\d{1,2})[/-](\d{1,2})(?:[/-](20\d{2}))?\b", normalized)
    if numeric:
        year = int(numeric.group(3) or reference_date.year)
        try:
            return date(year, int(numeric.group(2)), int(numeric.group(1)))
        except ValueError:
            return None

    named = re.search(
        r"\b(?:le\s+|du\s+|seance du\s+|activite du\s+|sortie du\s+)?"
        r"(\d{1,2})\s+(janvier|fevrier|mars|avril|mai|juin|juillet|aout|"
        r"septembre|octobre|novembre|decembre)(?:\s+(20\d{2}))?\b",
        normalized,
    )
    if named:
        year = int(named.group(3) or reference_date.year)
        try:
            return date(year, _MONTHS[named.group(2)], int(named.group(1)))
        except ValueError:
            return None
    return None


def _profile_proposal(question: str) -> tuple[dict[str, Any] | None, str | None]:
    """Extrait uniquement quelques valeurs numériques explicitement formulées."""
    patterns = (
        (r"\bma\s+vma\s+est\s+de\s+(\d+(?:[.,]\d+)?)\s*km/?h\b", "vma", "float"),
        (r"\b(?:mon\s+poids\s+est\s+de|je\s+pese)\s+(\d+(?:[.,]\d+)?)\s*kg\b", "weight_kg", "float"),
        (r"\bma\s+fc\s+max(?:imale)?\s+est\s+de\s+(\d{2,3})\s*(?:bpm)?\b", "max_heart_rate", "int"),
        (r"\bma\s+fc\s+au\s+repos\s+est\s+de\s+(\d{2,3})\s*(?:bpm)?\b", "resting_heart_rate", "int"),
        (r"\bje\s+mesure\s+(\d{2,3})\s*cm\b", "height_cm", "int"),
    )
    normalized = _normalize(question)
    for pattern, field_key, value_type in patterns:
        match = re.search(pattern, normalized)
        if match:
            raw = match.group(1).replace(",", ".")
            value = float(raw) if value_type == "float" else int(raw)
            return {
                "field_key": field_key,
                "value": value,
                "evidence": question.strip()[:200],
            }, None
    return None, (
        "Je n'ai pas identifié de valeur de profil exploitable avec certitude. "
        "Indique le champ et sa valeur avec son unité ; aucune donnée n'a été proposée."
    )


def build_coach_execution_plan(
    question: str,
    *,
    history: list[str] | None = None,
    assistant_history: list[str] | None = None,
    reference_date: date | None = None,
) -> CoachExecutionPlan:
    """Construit un plan d'appels Python sans demander au LLM de choisir les outils."""
    reference_date = reference_date or date.today()
    history = history or []
    assistant_history = assistant_history or []
    normalized = _normalize(question)
    conversation_users = [*history, question]

    # Les demandes d'accès direct aux fournisseurs sont refusées explicitement.
    if any(provider in normalized for provider in ("coros", "intervals.icu", "garmin", "suunto", "apple health")) and any(
        term in normalized for term in ("directement", "va chercher", "appelle l'api", "api fournisseur")
    ):
        return CoachExecutionPlan(clarification=(
            "Je ne consulte pas directement les plateformes externes. "
            "OpenCoach analyse uniquement les données déjà synchronisées dans son propre dossier. "
            "Sur combien de jours souhaites-tu analyser les données disponibles dans OpenCoach ?"
        ))

    # Le routeur conserve un catalogue de repli pour les formulations inconnues.
    # Ce catalogue ne constitue pas une autorisation d'exécuter tous ces outils.
    intent_markers = (
        "historique", "entrainement realise", "mes entrainements", "mes activites", "mes sorties", "charge", "atl", "ctl",
        "tsb", "recuperation", "recup", "sommeil", "hrv", "tendance", "evolution",
        "progression", "compare", "comparaison", "activite", "seance", "sortie du",
        "course", "ultra", "trail", "dossard", "preparation", "planning", "planifie",
        "programme", "semaine", "prochaine seance", "prochain entrainement", "seance suivante", "blessure", "douleur", "tendon", "malade", "maladie",
        "indisponible", "contrainte", "profil", "vma", "fc max", "frequence cardiaque",
        "zones cardiaques", "zone cardiaque", "etat de forme", "fatigue", "stress",
        "seuil", "poids", "je pese", "equipement", "chaussures", "mon poids",
    )
    last_assistant = _normalize(assistant_history[-1]) if assistant_history else ""
    clarification_follow_up = (
        len(question.split()) <= 5
        and bool(last_assistant)
        and any(
            cue in last_assistant
            for cue in (
                "combien de jours",
                "quelle duree",
                "duree des deux periodes",
                "deux periodes",
                "quelle date",
                "quelles dates",
                "date de debut",
                "date de fin",
                "precise la periode",
            )
        )
    )

    # Une réponse courte à une demande de clarification doit retrouver
    # l'intention métier initiale, même si un ou plusieurs tours utilisateur
    # intermédiaires ne contiennent que des paramètres (ex. « 2 jours »).
    prior_intent = ""
    if clarification_follow_up:
        for message in reversed(history[-8:]):
            normalized_message = _normalize(message)
            if any(marker in normalized_message for marker in intent_markers):
                prior_intent = message
                break
            # Seuls les tours intermédiaires contenant un paramètre explicite
            # (durée ou plage de dates) peuvent être traversés. Un « merci »,
            # une nouvelle question ou un échange terminé coupe l'héritage.
            if (
                extract_explicit_periods([message])
                or extract_explicit_date_range([message]) is not None
            ):
                continue
            break

    intent_context = _normalize(" ".join(part for part in (prior_intent, question) if part))
    routing_history = [prior_intent] if clarification_follow_up and prior_intent else history
    selected = set(select_coach_tools(
        question,
        history=routing_history,
        assistant_history=assistant_history,
        evidence_history=history,
    ))
    if not any(marker in intent_context for marker in intent_markers):
        return CoachExecutionPlan()

    periods = extract_explicit_periods(conversation_users, assistant_history)
    if any(term in intent_context for term in ("historique", "entrainement realise", "mes entrainements", "mes activites", "mes sorties", "bilan de ma semaine", "bilan de la semaine", "bilan hebdomadaire")) and "training_history" not in selected:
        if not periods:
            return CoachExecutionPlan(clarification="Sur combien de jours souhaites-tu que j'analyse ton historique ?")
        if not 1 <= periods[-1] <= 365:
            return CoachExecutionPlan(clarification="L'historique doit porter sur une période de 1 à 365 jours. Quelle période valide souhaites-tu ?")
    trend_comparison_requested = any(
        term in intent_context
        for term in (
            "tendance",
            "compare mes tendances",
            "evolution de mon entrainement",
            "compare les deux dernieres periodes",
            "compare les deux periodes",
            "comparaison des deux periodes",
        )
    ) or (
        "compare" in intent_context
        and any(term in intent_context for term in ("charge", "mon atl", "ctl", "tsb"))
    )
    if trend_comparison_requested and "training_trends" not in selected:
        if len(periods) < 2:
            return CoachExecutionPlan(clarification=(
                "Pour comparer la charge sur deux périodes, indique la durée des deux périodes "
                "(par exemple 7 jours puis 14 jours)."
            ))
    if any(term in intent_context for term in ("charge", "mon atl", "ctl", "tsb")) and "training_load" not in selected:
        if not periods:
            return CoachExecutionPlan(clarification="Sur combien de jours souhaites-tu analyser ta charge d'entraînement ?")
        if not 1 <= periods[-1] <= 90:
            return CoachExecutionPlan(clarification="La charge peut être analysée sur 1 à 90 jours. Quelle période valide souhaites-tu ?")
    if any(term in intent_context for term in ("seances planifiees", "seances prevues", "prochaines seances")) and "planned_sessions" not in selected:
        return CoachExecutionPlan(clarification="Quelles sont les dates de début et de fin à consulter pour tes séances planifiées ?")

    # Les demandes générales ou les intentions inconnues ne déclenchent aucune lecture métier.
    if not selected:
        periods = extract_explicit_periods(conversation_users, assistant_history)
        if any(term in normalized for term in ("historique", "entrainement realise", "mes entrainements", "mes activites", "mes sorties")):
            if not periods:
                return CoachExecutionPlan(clarification="Sur combien de jours souhaites-tu que j'analyse ton historique ?")
            if not 1 <= periods[-1] <= 365:
                return CoachExecutionPlan(clarification="L'historique doit porter sur une période de 1 à 365 jours. Quelle période valide souhaites-tu ?")
        if any(term in normalized for term in ("charge", "atl", "ctl", "tsb")):
            if not periods:
                return CoachExecutionPlan(clarification="Sur combien de jours souhaites-tu analyser ta charge d'entraînement ?")
            if not 1 <= periods[-1] <= 90:
                return CoachExecutionPlan(clarification="La charge peut être analysée sur 1 à 90 jours. Quelle période valide souhaites-tu ?")
        if any(term in normalized for term in ("tendance", "compare mes", "comparaison", "evolution de mon entrainement")):
            if len(periods) < 2:
                return CoachExecutionPlan(clarification="Pour comparer tes tendances, indique la durée des deux périodes (par exemple 7 jours et 14 jours).")
        if any(term in normalized for term in ("activite", "activité", "seance du", "séance du", "sortie du")):
            if extract_activity_date(question, reference_date) is None:
                return CoachExecutionPlan(clarification="Quelle est la date exacte de l'activité à détailler ?")
        return CoachExecutionPlan()

    calls: list[PlannedToolCall] = []

    # Une blessure ou une douleur impose d'abord la lecture des restrictions enregistrées.
    injury_terms = ("douleur", "mal au", "mal a", "tendon", "blessure", "blesse", "malade", "maladie", "indisponible")
    if "active_constraints" in selected and any(term in normalized for term in injury_terms):
        target_date = extract_activity_date(question, reference_date)
        safety_arguments = (
            {"target_date": target_date.isoformat()}
            if target_date is not None and target_date != reference_date
            else {}
        )
        safety_calls = [PlannedToolCall("active_constraints", safety_arguments)]
        if "recovery_status" in selected:
            safety_calls.append(PlannedToolCall("recovery_status", safety_arguments))
        return CoachExecutionPlan(tuple(safety_calls))

    # Une mise à jour de profil est proposée uniquement sur preuve textuelle exacte.
    if "propose_profile_data" in selected:
        proposal, clarification = _profile_proposal(question)
        if clarification:
            return CoachExecutionPlan(clarification=clarification)
        return CoachExecutionPlan((PlannedToolCall("propose_profile_data", proposal or {}),))

    periods = extract_explicit_periods(conversation_users, assistant_history)

    if "activity_detail" in selected:
        activity_id = re.search(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
            normalized,
        )
        if activity_id:
            calls.append(PlannedToolCall("activity_detail", {"activity_id": activity_id.group(0)}))
        else:
            activity_date = extract_activity_date(question, reference_date)
            if activity_date is None:
                latest_activity = any(
                    term in normalized
                    for term in ("derniere activite", "activite la plus recente", "derniere sortie")
                )
                if not latest_activity:
                    return CoachExecutionPlan(clarification="Quelle est la date exacte de l'activité à détailler ?")
                calls.append(PlannedToolCall("activity_detail", {"latest": True}))
            else:
                calls.append(PlannedToolCall("activity_detail", {"activity_date": activity_date.isoformat()}))

    if "training_history" in selected:
        if not periods:
            return CoachExecutionPlan(clarification="Sur combien de jours souhaites-tu que j'analyse ton historique ?")
        if not 1 <= periods[-1] <= 365:
            return CoachExecutionPlan(clarification="L'historique doit porter sur une période de 1 à 365 jours. Quelle période valide souhaites-tu ?")
        calls.append(PlannedToolCall("training_history", {"nb_days": periods[-1]}))

    # Une comparaison utilise training_trends, qui calcule déjà les métriques
    # des deux fenêtres. Ne lance pas en parallèle training_load : cela ajoute
    # des données de charge/planning/récupération hors comparaison et brouille
    # la synthèse demandée.
    if "training_load" in selected and not trend_comparison_requested:
        if not periods:
            return CoachExecutionPlan(clarification="Sur combien de jours souhaites-tu analyser ta charge d'entraînement ?")
        load_period = periods[-1]
        if not 1 <= load_period <= 90:
            return CoachExecutionPlan(clarification="La charge peut être analysée sur 1 à 90 jours. Quelle période valide souhaites-tu ?")
        calls.append(PlannedToolCall("training_load", {"nb_days": load_period}))

    if "training_trends" in selected:
        if len(periods) < 2:
            return CoachExecutionPlan(clarification="Pour comparer tes tendances, indique la durée des deux périodes (par exemple 7 jours et 14 jours).")
        first, second = periods[-2:]
        if not all(1 <= value <= 180 for value in (first, second)):
            return CoachExecutionPlan(clarification="Chaque période de comparaison doit être comprise entre 1 et 180 jours.")
        calls.append(PlannedToolCall("training_trends", {"nb_days": first, "comparison_days": second}))

    if "training_load" in selected and not trend_comparison_requested:
        # Une analyse de charge simple est contextualisée par le plan et la
        # récupération. Une comparaison reste strictement limitée aux deux
        # périodes demandées.
        calls.append(PlannedToolCall("recovery_analysis", {}))
        calls.append(PlannedToolCall("recovery_status", {}))
    elif not trend_comparison_requested and (
        "recovery_status" in selected or "recovery_analysis" in selected
    ):
        status_request = any(term in normalized for term in ("etat de recuperation", "readiness", "disponibilite aujourd", "suis-je pret"))
        if status_request and "recovery_status" in selected:
            calls.append(PlannedToolCall("recovery_status", {}))
        elif "recovery_analysis" in selected:
            calls.append(PlannedToolCall("recovery_analysis", {}))
        elif "recovery_status" in selected:
            calls.append(PlannedToolCall("recovery_status", {}))

    if "active_constraints" in selected and not calls:
        calls.append(PlannedToolCall("active_constraints", {}))

    # L'identifiant peut provenir du tour utilisateur où la course a été
    # sélectionnée ; il doit survivre à la clarification ultérieure sur la durée.
    race_evidence = " ".join(
        part for part in (prior_intent, question) if part
    ).casefold()
    race_id_match = None
    if "race_preparation_analysis" in selected:
        race_ids = list(re.finditer(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
            race_evidence,
        ))
        race_id_match = race_ids[-1] if race_ids else None

    if "race_calendar" in selected and not (
        "race_preparation_analysis" in selected and race_id_match is not None
    ):
        horizon = re.search(r"\b(\d{1,3})\s+(?:prochains?\s+)?jours\b", normalized)
        calls.append(PlannedToolCall(
            "race_calendar",
            {"horizon_days": int(horizon.group(1))} if horizon else {},
        ))

    # Une période explicite invalide ne doit pas désactiver silencieusement
    # l'analyse de préparation : demander une correction sans consulter l'outil.
    if (
        "preparation" in intent_context
        and "race_preparation_analysis" not in selected
        and periods
        and not 7 <= periods[-1] <= 180
    ):
        return CoachExecutionPlan(clarification=(
            "L'analyse de préparation nécessite une période de 7 à 180 jours. "
            "Quelle période valide souhaites-tu ?"
        ))

    if "race_preparation_analysis" in selected:
        # Une course ne peut être analysée qu'après identification explicite :
        # le calendrier fournit les identifiants, jamais un choix arbitraire.
        if not race_id_match:
            # La consultation du calendrier est conservée ; la sélection de la
            # course devra être confirmée avant toute analyse de préparation.
            pass
        elif not periods:
            return CoachExecutionPlan(clarification=(
                "Sur combien de jours d'historique souhaites-tu analyser ta préparation "
                "à cette course (7 à 180 jours) ?"
            ))
        elif not 7 <= periods[-1] <= 180:
            return CoachExecutionPlan(clarification=(
                "L'analyse de préparation nécessite une période de 7 à 180 jours. "
                "Quelle période valide souhaites-tu ?"
            ))
        else:
            calls.append(PlannedToolCall("race_preparation_analysis", {
                "race_id": race_id_match.group(0),
                "history_days": periods[-1],
            }))

    if "next_planned_session" in selected:
        calls.append(PlannedToolCall("next_planned_session", {}))

    if "planned_sessions" in selected:
        date_range = extract_explicit_date_range(conversation_users, assistant_history)
        if date_range is None:
            return CoachExecutionPlan(clarification="Quelles sont les dates de début et de fin à consulter ?")
        calls.append(PlannedToolCall("planned_sessions", {
            "start_date": date_range[0].isoformat(),
            "end_date": date_range[1].isoformat(),
        }))

    weekly_context_requested = any(
        term in intent_context
        for term in ("phase de la semaine", "objectif de la semaine", "cadre de la semaine", "quelle phase")
    )
    if not trend_comparison_requested and "weekly_plan_context" in selected and (
        "planned_sessions" not in selected or weekly_context_requested
    ):
        calls.append(PlannedToolCall("weekly_plan_context", {}))

    if "athlete_training_profile" in selected and not any(
        call.name == "propose_profile_data" for call in calls
    ):
        calls.append(PlannedToolCall("athlete_training_profile", {}))

    # Les flux à plusieurs étapes nécessitent une sélection humaine avant le second outil.
    if "session_execution_review" in selected:
        return CoachExecutionPlan(clarification=(
            "Pour comparer une séance prévue à sa réalisation, indique la séance concernée "
            "ou sélectionne-la dans le planning OpenCoach. Aucune comparaison n'a été lancée."
        ))

    if not calls:
        return CoachExecutionPlan()
    return CoachExecutionPlan(tuple(calls))
