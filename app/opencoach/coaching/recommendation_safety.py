"""Garde-fous métier appliqués aux recommandations d'entraînement."""

from __future__ import annotations

from collections.abc import Mapping


def blocked_running_recommendation_message(
    restriction: Mapping[str, object] | None,
) -> str | None:
    """Retourne le message de blocage si la course à pied est interdite.

    Une absence de restriction ou une donnée mal formée ne crée jamais
    artificiellement une interdiction. La disponibilité des données est
    contrôlée séparément par le cas d'usage appelant.
    """
    if restriction is None or restriction.get("blocked") is not True:
        return None

    message = restriction.get("message")
    if isinstance(message, str) and message.strip():
        return message

    return (
        "Une restriction active dans OpenCoach interdit la course à pied "
        "pour la date concernée."
    )
