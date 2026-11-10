"""Vérification déterministe de la provenance des périodes demandées au coach."""
from __future__ import annotations
import re
import unicodedata

_DURATION_RE = re.compile(
    r"\b(?P<value>\d{1,3}|un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|quatorze|quinze|vingt|trente)\s*(?P<unit>jours?|j|semaines?|sem\.?|mois)\b",
    re.IGNORECASE,
)
_WORD_NUMBERS = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "quatorze": 14, "quinze": 15, "vingt": 20, "trente": 30}
_PERIOD_RULES = {"training_history": ("nb_days", 1, 365, "historique"), "training_load": ("nb_days", 1, 90, "charge")}

def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))

def extract_explicit_periods(
    user_messages: list[str],
    assistant_messages: list[str] | None = None,
) -> list[int]:
    """N'extrait que la dernière demande utilisateur pour éviter les périodes périmées."""
    if not user_messages:
        return []

    latest = _normalize(user_messages[-1])
    periods = []
    for match in _DURATION_RE.finditer(latest):
        raw_value = match.group("value")
        value = int(raw_value) if raw_value.isdigit() else _WORD_NUMBERS[raw_value]
        unit = match.group("unit")
        if unit.startswith("sem"):
            value *= 7
        elif unit == "mois":
            continue
        periods.append(value)

    # Un nombre isolé n'est une réponse de période que si le tour assistant
    # précédent a explicitement demandé cette précision.
    if not periods and assistant_messages:
        last_assistant = _normalize(assistant_messages[-1])
        bare_number = re.fullmatch(r"(?:sur\s+)?(\d{1,3})", latest.strip())
        clarification_requested = bool(
            re.search(r"combien de jours|quelle duree|duree des deux periodes", last_assistant)
        )
        if bare_number and clarification_requested:
            periods.append(int(bare_number.group(1)))
    return periods

def validate_period_argument_evidence(tool_name: str, arguments: dict, user_messages: list[str], assistant_messages: list[str] | None = None) -> str | None:
    """Bloque les fenêtres temporelles non fournies ou altérées par le modèle."""
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
        return "Sur combien de jours souhaites-tu analyser ta charge d'entraînement ?"
    expected = periods[-1]
    if expected < minimum or expected > maximum:
        return f"La période demandée ({expected} jours) dépasse les limites de cet outil ({minimum} à {maximum} jours). Indique une période valide ; aucune donnée n'a été consultée."
    supplied = arguments.get(argument_name)
    if supplied != expected:
        return f"Tu as indiqué {expected} jours pour {label}, mais le modèle a proposé {supplied!r}. Je n'ai pas lancé l'analyse. Confirme la période souhaitée."
    return None
