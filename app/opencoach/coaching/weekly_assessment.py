"""Évaluation hebdomadaire synthétique du Coach.

Ce module transforme la projection hebdomadaire déterministe
en informations directement exploitables par les interfaces Coach.

Il ne modifie aucune séance.
Il décrit uniquement l'état courant de la semaine et indique
si une adaptation pourrait être proposée à l'athlète.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.training.weekly_load_projection import (
    WeeklyLoadProjection,
)


class CoachWeeklyStatus(StrEnum):
    """Position de la projection par rapport à la cible."""

    ALIGNED = "aligned"
    UNDER_TARGET = "under_target"
    OVER_TARGET = "over_target"
    UNKNOWN = "unknown"


class CoachHistoryConfidenceLevel(StrEnum):
    """Niveau lisible de confiance dans la référence historique."""

    LOW = "low"
    MODERATE = "moderate"
    GOOD = "good"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class CoachWeeklyAssessment:
    """Synthèse déterministe de la semaine courante."""

    status: CoachWeeklyStatus

    target_load: float | None
    actual_load_to_date: float
    remaining_planned_load: float
    projected_week_load: float

    projected_gap: float | None
    projected_gap_percent: float | None

    remaining_days: int
    remaining_sessions_count: int

    adaptation_opportunity: bool
    adaptation_direction: str | None

    history_window_days: int
    history_confidence: float
    history_confidence_level: (
        CoachHistoryConfidenceLevel
    )

    headline: str
    analysis: str
    instruction: str


def build_coach_weekly_assessment(
    *,
    projection: WeeklyLoadProjection,
    history_window_days: int,
    history_confidence: float,
) -> CoachWeeklyAssessment:
    """Construit l'évaluation hebdomadaire destinée au Coach."""

    if history_window_days <= 0:
        raise ValueError(
            "La fenêtre historique doit être positive."
        )

    if not 0.0 <= history_confidence <= 1.0:
        raise ValueError(
            "La confiance historique doit être comprise "
            "entre 0 et 1."
        )

    status = _resolve_status(
        projection
    )

    confidence_level = (
        _resolve_confidence_level(
            history_confidence
        )
    )

    headline = _build_headline(
        status=status,
    )

    analysis = _build_analysis(
        projection=projection,
        status=status,
        history_window_days=(
            history_window_days
        ),
        history_confidence_level=(
            confidence_level
        ),
    )

    instruction = _build_instruction(
        projection=projection,
        status=status,
    )

    return CoachWeeklyAssessment(
        status=status,

        target_load=projection.target_load,
        actual_load_to_date=(
            projection.actual_load_to_date
        ),
        remaining_planned_load=(
            projection.remaining_planned_load
        ),
        projected_week_load=(
            projection.projected_week_load
        ),

        projected_gap=(
            projection.projected_gap
        ),
        projected_gap_percent=(
            projection.projected_gap_percent
        ),

        remaining_days=(
            projection.remaining_days
        ),
        remaining_sessions_count=(
            projection.remaining_sessions_count
        ),

        adaptation_opportunity=(
            projection.adaptation_opportunity
        ),
        adaptation_direction=(
            projection.adaptation_direction
        ),

        history_window_days=(
            history_window_days
        ),
        history_confidence=round(
            history_confidence,
            2,
        ),
        history_confidence_level=(
            confidence_level
        ),

        headline=headline,
        analysis=analysis,
        instruction=instruction,
    )


def _resolve_status(
    projection: WeeklyLoadProjection,
) -> CoachWeeklyStatus:
    gap_percent = (
        projection.projected_gap_percent
    )

    if (
        projection.target_load is None
        or gap_percent is None
    ):
        return CoachWeeklyStatus.UNKNOWN

    if gap_percent < -15.0:
        return (
            CoachWeeklyStatus.UNDER_TARGET
        )

    if gap_percent > 15.0:
        return (
            CoachWeeklyStatus.OVER_TARGET
        )

    return CoachWeeklyStatus.ALIGNED


def _resolve_confidence_level(
    confidence: float,
) -> CoachHistoryConfidenceLevel:
    if confidence < 0.50:
        return (
            CoachHistoryConfidenceLevel.LOW
        )

    if confidence < 0.75:
        return (
            CoachHistoryConfidenceLevel.MODERATE
        )

    if confidence < 1.0:
        return (
            CoachHistoryConfidenceLevel.GOOD
        )

    return (
        CoachHistoryConfidenceLevel.HIGH
    )


def _build_headline(
    *,
    status: CoachWeeklyStatus,
) -> str:
    if status is CoachWeeklyStatus.ALIGNED:
        return "Votre semaine est dans la trajectoire"

    if status is CoachWeeklyStatus.UNDER_TARGET:
        return "Votre semaine est sous la cible prévue"

    if status is CoachWeeklyStatus.OVER_TARGET:
        return "Votre semaine dépasse la cible prévue"

    return "La trajectoire hebdomadaire est en cours d'apprentissage"


def _build_analysis(
    *,
    projection: WeeklyLoadProjection,
    status: CoachWeeklyStatus,
    history_window_days: int,
    history_confidence_level: (
        CoachHistoryConfidenceLevel
    ),
) -> str:
    history_note = (
        _build_history_note(
            history_window_days=(
                history_window_days
            ),
            confidence_level=(
                history_confidence_level
            ),
        )
    )

    if status is CoachWeeklyStatus.UNKNOWN:
        return (
            "OpenCoach ne dispose pas encore d'une cible "
            "hebdomadaire suffisamment exploitable pour "
            "comparer la projection de la semaine. "
            + history_note
        )

    gap_percent = (
        projection.projected_gap_percent
    )

    assert gap_percent is not None

    if status is CoachWeeklyStatus.ALIGNED:
        return (
            "En tenant compte de la charge déjà réalisée "
            "et des séances encore prévues, votre projection "
            f"termine à {abs(gap_percent):.1f} % de la cible. "
            "La trajectoire actuelle est cohérente. "
            + history_note
        )

    if status is CoachWeeklyStatus.UNDER_TARGET:
        return (
            "La charge déjà réalisée et les séances restantes "
            f"projettent la semaine à {abs(gap_percent):.1f} % "
            "sous la cible. "
            f"Il reste {projection.remaining_days} jour(s) "
            f"et {projection.remaining_sessions_count} séance(s) "
            "planifiée(s). "
            + history_note
        )

    return (
        "La charge déjà réalisée et les séances restantes "
        f"projettent la semaine à {abs(gap_percent):.1f} % "
        "au-dessus de la cible. "
        f"Il reste {projection.remaining_days} jour(s) "
        f"et {projection.remaining_sessions_count} séance(s) "
        "planifiée(s). "
        + history_note
    )


def _build_instruction(
    *,
    projection: WeeklyLoadProjection,
    status: CoachWeeklyStatus,
) -> str:
    if status is CoachWeeklyStatus.ALIGNED:
        return (
            "Conservez le programme prévu. "
            "Aucune adaptation de charge n'est nécessaire "
            "pour le moment."
        )

    if status is CoachWeeklyStatus.UNDER_TARGET:
        if projection.adaptation_opportunity:
            return (
                "Une adaptation de la fin de semaine peut être "
                "envisagée. OpenCoach ne modifiera pas les séances "
                "sans votre validation."
            )

        return (
            "Ne cherchez pas à rattraper artificiellement le déficit. "
            "Conservez le programme restant."
        )

    if status is CoachWeeklyStatus.OVER_TARGET:
        if projection.adaptation_opportunity:
            return (
                "Un allègement de la fin de semaine peut être "
                "envisagé afin de revenir vers la zone cible."
            )

        return (
            "Conservez le programme restant sans ajouter "
            "de charge supplémentaire."
        )

    return (
        "Conservez le programme actuel pendant qu'OpenCoach "
        "consolide votre référence hebdomadaire."
    )


def _build_history_note(
    *,
    history_window_days: int,
    confidence_level: (
        CoachHistoryConfidenceLevel
    ),
) -> str:
    weeks = max(
        1,
        round(
            history_window_days
            / 7
        ),
    )

    if weeks == 1:
        period = "1 semaine"
    else:
        period = f"{weeks} semaines"

    if (
        confidence_level
        is CoachHistoryConfidenceLevel.LOW
    ):
        return (
            "La référence repose encore sur "
            f"{period} d'historique et reste provisoire."
        )

    if (
        confidence_level
        is CoachHistoryConfidenceLevel.MODERATE
    ):
        return (
            "La référence repose sur "
            f"{period} d'historique et gagne en stabilité."
        )

    if (
        confidence_level
        is CoachHistoryConfidenceLevel.GOOD
    ):
        return (
            "La référence repose sur "
            f"{period} d'historique avec une bonne confiance."
        )

    return (
        "La référence hebdomadaire dispose désormais "
        "d'un historique complet et stable."
    )
