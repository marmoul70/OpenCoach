"""Vérification déterministe de la provenance des périodes demandées au coach."""
from __future__ import annotations
import re
import unicodedata
from datetime import date

_DURATION_RE = re.compile(
    r"\b(?P<value>\d{1,3}|un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|quatorze|quinze|vingt|trente)\s*(?:(?:derniers?|dernieres?|precedents?|precedentes?)\s*)?(?P<unit>jours?|j|semaines?|sem\.?|mois)\b",
    re.IGNORECASE,
)
_WORD_NUMBERS = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "quatorze": 14, "quinze": 15, "vingt": 20, "trente": 30}
_MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}
_ISO_DATE_RE = re.compile(r"\\b20\\d{2}-\\d{2}-\\d{2}\\b")
_FRENCH_DATE_RANGE_RE = re.compile(
    r"\\bdu\\s+(?P<start_day>\\d{1,2})(?:\\s+(?P<start_month>janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre))?\\s+au\\s+(?P<end_day>\\d{1,2})\\s+(?P<end_month>janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\\s+(?P<year>20\\d{2})\\b"
)
_PERIOD_RULES = {
    "training_history": ("nb_days", 1, 365, "historique"),
    "training_load": ("nb_days", 1, 90, "charge"),
    "race_preparation_analysis": ("history_days", 7, 180, "préparation"),
}

def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))

def _extract_duration_values(text: str) -> list[int]:
    values: list[int] = []
    for match in _DURATION_RE.finditer(_normalize(text)):
        raw_value = match.group("value")
        value = int(raw_value) if raw_value.isdigit() else _WORD_NUMBERS[raw_value]
        unit = match.group("unit")
        if unit.startswith("sem"):
            value *= 7
        elif unit == "mois":
            continue
        values.append(value)
    return values


def extract_explicit_periods(
    user_messages: list[str],
    assistant_messages: list[str] | None = None,
) -> list[int]:
    """Extrait les durées explicites du dernier tour, avec suivi conversationnel borné."""
    if not user_messages:
        return []

    latest = _normalize(user_messages[-1]).strip()
    last_assistant = _normalize(assistant_messages[-1]) if assistant_messages else ""
    clarification_requested = bool(
        re.search(
            r"combien de jours|quelle duree|duree des deux periodes|quelle periode|sur combien",
            last_assistant,
        )
    )
    periods = _extract_duration_values(latest)
    if periods:
        # Pour une comparaison, le second tour peut ne contenir que la
        # deuxième durée : on conserve alors la première durée du tour
        # précédent uniquement si l'assistant a demandé les deux périodes.
        if (
            len(periods) == 1
            and "duree des deux periodes" in last_assistant
            and len(user_messages) >= 2
        ):
            previous_periods = _extract_duration_values(user_messages[-2])
            if previous_periods:
                return [previous_periods[-1], periods[0]]
        return periods
    bare_number = re.fullmatch(r"(?:sur\s+)?(\d{1,3})", latest)
    if bare_number and clarification_requested:
        return [int(bare_number.group(1))]

    # Un suivi très court peut reprendre la période du tour utilisateur
    # immédiatement précédent, sauf si l'assistant vient de demander une
    # nouvelle précision temporelle. Une nouvelle demande complète ne
    # réutilise jamais une ancienne période.
    if (
        not clarification_requested
        and len(latest.split()) <= 5
        and len(user_messages) >= 2
    ):
        return _extract_duration_values(user_messages[-2])

    return []


def extract_explicit_date_range(
    user_messages: list[str],
    assistant_messages: list[str] | None = None,
) -> tuple[date, date] | None:
    """Extrait une plage de dates explicitement fournie, avec suivi court borné."""
    if not user_messages:
        return None

    latest = _normalize(user_messages[-1])
    match = _FRENCH_DATE_RANGE_RE.search(latest)
    if match:
        year = int(match.group("year"))
        end_month = _MONTHS[match.group("end_month")]
        start_month = _MONTHS.get(match.group("start_month"), end_month)
        try:
            return (
                date(year, start_month, int(match.group("start_day"))),
                date(year, end_month, int(match.group("end_day"))),
            )
        except ValueError:
            return None

    iso_dates = _ISO_DATE_RE.findall(latest)
    if len(iso_dates) >= 2:
        try:
            return date.fromisoformat(iso_dates[0]), date.fromisoformat(iso_dates[1])
        except ValueError:
            return None

    last_assistant = _normalize(assistant_messages[-1]) if assistant_messages else ""
    clarification_requested = bool(
        re.search(r"quelles dates|quelle periode|date de debut|date de fin", last_assistant)
    )
    if (
        not clarification_requested
        and len(latest.split()) <= 5
        and len(user_messages) >= 2
    ):
        return extract_explicit_date_range([user_messages[-2]])

    return None

def validate_period_argument_evidence(tool_name: str, arguments: dict, user_messages: list[str], assistant_messages: list[str] | None = None) -> str | None:
    """Bloque les fenêtres temporelles non fournies ou altérées par le modèle."""
    if tool_name == "planned_sessions":
        date_range = extract_explicit_date_range(user_messages, assistant_messages)
        if date_range is None:
            return "Quelles sont les dates de début et de fin à consulter ? Je n'ai lancé aucune recherche."
        try:
            supplied_range = (
                date.fromisoformat(str(arguments.get("start_date"))),
                date.fromisoformat(str(arguments.get("end_date"))),
            )
        except (TypeError, ValueError):
            return "Les dates proposées ne sont pas valides. Indique une date de début et une date de fin."
        if supplied_range != date_range:
            return "Les dates proposées ne correspondent pas à la période que tu as indiquée. Confirme les dates souhaitées ; aucune recherche n'a été lancée."
        return None

    if tool_name not in (*_PERIOD_RULES, "training_trends"):
        return None
    periods = extract_explicit_periods(user_messages, assistant_messages)
    if tool_name == "training_trends":
        if len(periods) < 2:
            return "Pour comparer tes tendances, indique la durée des deux périodes (par exemple 7 jours et 14 jours). Je n'ai lancé aucun calcul."
        expected = periods[-2:]
        supplied = [arguments.get("nb_days"), arguments.get("comparison_days")]
        if supplied != expected:
            return "Les durées proposées par le modèle ne correspondent pas aux deux périodes que tu as indiquées. Précise les deux durées à comparer ; aucun calcul n'a été lancé."
        if any(value < 1 or value > 180 for value in expected):
            return "Chaque période doit être comprise entre 1 et 180 jours. Quelles durées valides souhaites-tu comparer ?"
        return None
    argument_name, minimum, maximum, label = _PERIOD_RULES[tool_name]
    if not periods:
        if tool_name == "training_history":
            return "Sur combien de jours souhaites-tu que j'analyse ton historique ?"
        if tool_name == "training_load":
            return "Sur combien de jours souhaites-tu analyser ta charge d'entraînement ?"
        return "Sur combien de jours d'historique souhaites-tu analyser ta préparation à cette course ?"
    expected = periods[-1]
    if expected < minimum or expected > maximum:
        return f"La période demandée ({expected} jours) dépasse les limites de cet outil ({minimum} à {maximum} jours). Indique une période valide ; aucune donnée n'a été consultée."
    supplied = arguments.get(argument_name)
    if supplied != expected:
        return f"Tu as indiqué {expected} jours pour {label}, mais le modèle a proposé {supplied!r}. Je n'ai pas lancé l'analyse. Confirme la période souhaitée."
    return None
