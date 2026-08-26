"""Adaptation d'une séance après accord explicite de l'athlète.

Ce module applique une adaptation prudente à une séance planifiée
lorsque l'athlète a accepté une proposition issue de son check-in.

Il ne pose aucun diagnostic et ne modifie pas la trajectoire globale.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)
from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
)
from opencoach.models import (
    TrainingSession,
)


class DailySessionAdaptationError(
    RuntimeError
):
    """Erreur lors d'une adaptation quotidienne."""


@dataclass(frozen=True, slots=True)
class DailySessionAdaptationResult:
    """Résultat d'une adaptation autorisée."""

    original: TrainingSession

    adapted: TrainingSession

    changed: bool

    reasons: tuple[
        str,
        ...
    ]


def adapt_daily_training_session(
    *,
    session: TrainingSession,
    checkin: AthleteDailyCheckIn,
    proposal: CoachAdaptationProposal,
) -> DailySessionAdaptationResult:
    """Adapte une séance après acceptation explicite."""

    if not proposal.adaptation_authorized:
        raise DailySessionAdaptationError(
            "L'athlète n'a pas autorisé "
            "l'adaptation de la séance."
        )

    if session.status != "planned":
        raise DailySessionAdaptationError(
            "Seule une séance encore planifiée "
            "peut être adaptée."
        )

    reasons: list[str] = []

    # --------------------------------------------------------
    # Niveau d'adaptation
    # --------------------------------------------------------

    strong_reduction = (
        checkin.illness
        or checkin.energy_rating <= 2
        or checkin.pain_wellness_rating <= 2
    )

    moderate_reduction = (
        not strong_reduction
        and (
            checkin.energy_rating == 3
            or checkin.pain_wellness_rating == 3
        )
    )

    if not (
        strong_reduction
        or moderate_reduction
    ):
        return DailySessionAdaptationResult(
            original=session,
            adapted=session,
            changed=False,
            reasons=(),
        )

    # --------------------------------------------------------
    # Réduction forte
    # --------------------------------------------------------

    if strong_reduction:
        if checkin.illness:
            reasons.append(
                "Maladie déclarée."
            )

        if checkin.energy_rating <= 2:
            reasons.append(
                "Énergie déclarée faible."
            )

        if checkin.pain_wellness_rating <= 2:
            reasons.append(
                "Douleur ou gêne importante déclarée."
            )

        adapted = replace(
            session,
            type="recovery",
            title=(
                "Séance de récupération adaptée"
            ),
            description=(
                "Séance allégée après accord explicite "
                "de l'athlète suite au check-in quotidien."
            ),
            duration_minutes=min(
                session.duration_minutes,
                30,
            ),
            intensity="easy",
            heart_rate_zone=None,
        )

        return DailySessionAdaptationResult(
            original=session,
            adapted=adapted,
            changed=(
                adapted != session
            ),
            reasons=tuple(
                reasons
            ),
        )

    # --------------------------------------------------------
    # Réduction modérée
    # --------------------------------------------------------

    if checkin.energy_rating == 3:
        reasons.append(
            "Énergie moyenne déclarée."
        )

    if checkin.pain_wellness_rating == 3:
        reasons.append(
            "Douleur ou gêne modérée déclarée."
        )

    hard_session = (
        session.intensity.lower()
        in {
            "hard",
            "very_hard",
            "high",
        }
    )

    if hard_session:
        adapted = replace(
            session,
            type="aerobic_easy",
            title=(
                "Endurance facile adaptée"
            ),
            description=(
                "Séance qualitative remplacée par "
                "une endurance facile après accord "
                "explicite de l'athlète."
            ),
            duration_minutes=min(
                session.duration_minutes,
                45,
            ),
            intensity="easy",
            heart_rate_zone=None,
        )

    else:
        reduced_duration = max(
            20,
            round(
                session.duration_minutes
                * 0.8
            ),
        )

        reduced_duration = min(
            reduced_duration,
            session.duration_minutes,
        )

        adapted = replace(
            session,
            duration_minutes=(
                reduced_duration
            ),
        )

    return DailySessionAdaptationResult(
        original=session,
        adapted=adapted,
        changed=(
            adapted != session
        ),
        reasons=tuple(
            reasons
        ),
    )
