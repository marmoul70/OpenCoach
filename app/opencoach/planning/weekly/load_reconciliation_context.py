"""Contexte associé à une réconciliation de charge hebdomadaire.

Ce module décrit pourquoi la charge réellement effectuée diffère
éventuellement de la charge prévue.

Il ne décide pas encore comment la trajectoire doit être modifiée.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.planning.weekly.load_reconciliation import (
    LoadReconciliationStatus,
    WeeklyLoadReconciliation,
)


class LoadDeviationCause(StrEnum):
    """Cause principale expliquant l'écart de charge."""

    NONE = "none"

    PROFESSIONAL_CONSTRAINT = "professional_constraint"
    PERSONAL_CONSTRAINT = "personal_constraint"

    ATHLETE_CHOICE = "athlete_choice"

    FATIGUE = "fatigue"
    ILLNESS = "illness"
    INJURY = "injury"

    SPORT_EVENT = "sport_event"

    INCOMPLETE_DATA = "incomplete_data"

    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ContextualWeeklyLoadReconciliation:
    """Réconciliation enrichie de son contexte."""

    reconciliation: WeeklyLoadReconciliation

    cause: LoadDeviationCause

    athlete_imposed: bool = False

    note: str | None = None

    def __post_init__(self) -> None:
        on_target = (
            self.reconciliation.status
            is LoadReconciliationStatus.ON_TARGET
        )

        if (
            on_target
            and self.cause is not LoadDeviationCause.NONE
        ):
            raise ValueError(
                "Une semaine conforme à la cible ne doit pas définir "
                "de cause d'écart."
            )

        if (
            not on_target
            and self.cause is LoadDeviationCause.NONE
        ):
            raise ValueError(
                "Un écart significatif doit définir une cause."
            )


def contextualize_weekly_load_reconciliation(
    *,
    reconciliation: WeeklyLoadReconciliation,
    cause: LoadDeviationCause | None = None,
    athlete_imposed: bool = False,
    note: str | None = None,
) -> ContextualWeeklyLoadReconciliation:
    """Ajoute un contexte explicatif à une réconciliation."""

    if (
        reconciliation.status
        is LoadReconciliationStatus.ON_TARGET
    ):
        effective_cause = LoadDeviationCause.NONE
    else:
        effective_cause = (
            cause
            if cause is not None
            else LoadDeviationCause.UNKNOWN
        )

    return ContextualWeeklyLoadReconciliation(
        reconciliation=reconciliation,
        cause=effective_cause,
        athlete_imposed=athlete_imposed,
        note=note,
    )
