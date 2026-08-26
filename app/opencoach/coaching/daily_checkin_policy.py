"""Politique de conseil issue du check-in quotidien.

Cette couche observe les déclarations de l'athlète et détermine
le niveau d'attention du coach.

Elle ne modifie jamais automatiquement une séance.

L'athlète conserve la décision d'accepter ou non une adaptation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
)


class CheckInCoachAction(StrEnum):
    """Réaction proposée par le coach."""

    NONE = "none"

    MONITOR = "monitor"

    OFFER_ADAPTATION = (
        "offer_adaptation"
    )

    STRONGLY_RECOMMEND_ADAPTATION = (
        "strongly_recommend_adaptation"
    )


@dataclass(frozen=True, slots=True)
class DailyCheckInAssessment:
    """Analyse d'un check-in par le coach."""

    action: CheckInCoachAction

    reasons: tuple[
        str,
        ...
    ]

    adaptation_requires_athlete_decision: bool

    increased_debrief_attention: bool

    illness_reported: bool

    unavailable_reported: bool


def assess_daily_checkin(
    checkin: AthleteDailyCheckIn,
) -> DailyCheckInAssessment:
    """Analyse un check-in sans modifier le programme."""

    reasons: list[
        str
    ] = []

    action = (
        CheckInCoachAction.NONE
    )

    # --------------------------------------------------------
    # Indisponibilité
    # --------------------------------------------------------

    if checkin.unavailable:
        reasons.append(
            "Athlète déclaré indisponible."
        )

        action = (
            CheckInCoachAction
            .STRONGLY_RECOMMEND_ADAPTATION
        )

    # --------------------------------------------------------
    # Maladie
    # --------------------------------------------------------

    if checkin.illness:
        reasons.append(
            "Maladie déclarée."
        )

        action = _max_action(
            action,
            CheckInCoachAction
            .STRONGLY_RECOMMEND_ADAPTATION,
        )

    # --------------------------------------------------------
    # Énergie / fatigue
    # --------------------------------------------------------

    if checkin.energy_rating == 4:
        reasons.append(
            "Légère fatigue déclarée."
        )

        action = _max_action(
            action,
            CheckInCoachAction.MONITOR,
        )

    elif checkin.energy_rating == 3:
        reasons.append(
            "Fatigue modérée déclarée."
        )

        action = _max_action(
            action,
            CheckInCoachAction.OFFER_ADAPTATION,
        )

    elif checkin.energy_rating <= 2:
        reasons.append(
            "Fatigue importante déclarée."
        )

        action = _max_action(
            action,
            CheckInCoachAction
            .STRONGLY_RECOMMEND_ADAPTATION,
        )

    # --------------------------------------------------------
    # Douleur / blessure
    # --------------------------------------------------------

    if checkin.pain_wellness_rating == 4:
        reasons.append(
            "Gêne légère déclarée."
        )

        action = _max_action(
            action,
            CheckInCoachAction.MONITOR,
        )

    elif checkin.pain_wellness_rating == 3:
        reasons.append(
            "Douleur ou gêne modérée déclarée."
        )

        action = _max_action(
            action,
            CheckInCoachAction.OFFER_ADAPTATION,
        )

    elif checkin.pain_wellness_rating <= 2:
        reasons.append(
            "Douleur ou gêne importante déclarée."
        )

        action = _max_action(
            action,
            CheckInCoachAction
            .STRONGLY_RECOMMEND_ADAPTATION,
        )

    if checkin.pain_locations:
        locations = ", ".join(
            (
                f"{location.area.value}"
                f":{location.side.value}"
            )
            for location
            in checkin.pain_locations
        )

        reasons.append(
            "Localisation déclarée : "
            f"{locations}."
        )

    requires_decision = (
        action
        in {
            CheckInCoachAction.OFFER_ADAPTATION,
            CheckInCoachAction
            .STRONGLY_RECOMMEND_ADAPTATION,
        }
    )

    increased_debrief_attention = (
        checkin.energy_rating < 5
        or checkin.pain_wellness_rating < 5
        or checkin.illness
    )

    return DailyCheckInAssessment(
        action=action,
        reasons=tuple(
            reasons
        ),
        adaptation_requires_athlete_decision=(
            requires_decision
        ),
        increased_debrief_attention=(
            increased_debrief_attention
        ),
        illness_reported=checkin.illness,
        unavailable_reported=(
            checkin.unavailable
        ),
    )


_ACTION_PRIORITY = {
    CheckInCoachAction.NONE: 0,
    CheckInCoachAction.MONITOR: 1,
    CheckInCoachAction.OFFER_ADAPTATION: 2,
    CheckInCoachAction.STRONGLY_RECOMMEND_ADAPTATION: 3,
}


def _max_action(
    first: CheckInCoachAction,
    second: CheckInCoachAction,
) -> CheckInCoachAction:
    """Conserve le niveau de prudence le plus élevé."""

    if (
        _ACTION_PRIORITY[second]
        > _ACTION_PRIORITY[first]
    ):
        return second

    return first
