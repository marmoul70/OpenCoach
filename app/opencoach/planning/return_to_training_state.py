"""État temporel du retour progressif à l'entraînement.

Ce module détermine si la période minimale de reprise imposée par
la trajectoire est encore active après un événement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .return_to_training_policy import (
    ReturnToTrainingPolicy,
)


@dataclass(frozen=True, slots=True)
class ReturnToTrainingState:
    """État calculé d'une période de reprise."""

    active: bool

    week_index: int | None

    minimum_weeks: int

    return_start_date: date

    minimum_end_date: date

    minimum_completed: bool


def calculate_return_to_training_state(
    *,
    planning_date: date,
    event_end_date: date,
    policy: ReturnToTrainingPolicy,
) -> ReturnToTrainingState:
    """Calcule l'état temporel de la reprise."""

    return_start_date = (
        event_end_date
        + timedelta(days=1)
    )

    minimum_end_date = (
        return_start_date
        + timedelta(
            weeks=policy.minimum_weeks,
        )
    )

    if planning_date < return_start_date:
        return ReturnToTrainingState(
            active=False,
            week_index=None,
            minimum_weeks=policy.minimum_weeks,
            return_start_date=return_start_date,
            minimum_end_date=minimum_end_date,
            minimum_completed=False,
        )

    elapsed_days = (
        planning_date
        - return_start_date
    ).days

    minimum_completed = (
        planning_date
        >= minimum_end_date
    )

    week_index = (
        elapsed_days // 7
    ) + 1

    return ReturnToTrainingState(
        active=not minimum_completed,
        week_index=week_index,
        minimum_weeks=policy.minimum_weeks,
        return_start_date=return_start_date,
        minimum_end_date=minimum_end_date,
        minimum_completed=minimum_completed,
    )
