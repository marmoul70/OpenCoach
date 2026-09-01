"""Construction du rappel de séance du lendemain."""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.models import (
    TrainingSession,
)
from opencoach.weather.training_advisory import (
    TrainingWeatherAdvice,
)


@dataclass(
    frozen=True,
    slots=True,
)
class TomorrowSessionReminder:
    title: str
    body: str
    url: str


def build_tomorrow_session_reminder(
    session: TrainingSession,
    *,
    weather_advice: (
        TrainingWeatherAdvice
        | None
    ) = None,
) -> TomorrowSessionReminder:
    """Construit le texte de la notification."""

    session_label = (
        _session_label(
            session
        )
    )

    body = (
        "Demain, "
        f"{session_label}"
        f" de {session.duration_minutes} min"
        " prévue."
    )

    if (
        weather_advice is not None
        and weather_advice.message
    ):
        body += (
            " "
            + weather_advice.message
        )

    return TomorrowSessionReminder(
        title="Séance de demain",
        body=body,
        url=(
            "/training"
            f"?session={session.id}"
            f"&date={session.date.isoformat()}"
        ),
    )


def _session_label(
    session: TrainingSession,
) -> str:
    normalized = (
        f"{session.type} "
        f"{session.title}"
    ).lower()

    if any(
        term in normalized
        for term in (
            "interval",
            "fraction",
            "vo2",
            "vma",
        )
    ):
        return (
            "une séance fractionnée"
        )

    if any(
        term in normalized
        for term in (
            "threshold",
            "seuil",
            "tempo",
        )
    ):
        return (
            "une séance au seuil"
        )

    if any(
        term in normalized
        for term in (
            "long",
            "sortie longue",
        )
    ):
        return (
            "une sortie longue"
        )

    if any(
        term in normalized
        for term in (
            "recovery",
            "récup",
        )
    ):
        return (
            "une séance de récupération"
        )

    if any(
        term in normalized
        for term in (
            "strength",
            "renfo",
            "musculation",
        )
    ):
        return (
            "une séance de renforcement"
        )

    if any(
        term in normalized
        for term in (
            "easy",
            "endurance",
            "ef",
        )
    ):
        return (
            "une séance EF"
        )

    if session.title.strip():
        return (
            f"la séance « "
            f"{session.title.strip()}"
            " »"
        )

    return (
        "une séance d’entraînement"
    )
