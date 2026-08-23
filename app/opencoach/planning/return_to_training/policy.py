"""Politique déterministe de retour progressif à l'entraînement.

Ce module détermine le cadre minimal de reprise après une interruption
significative. Il ne génère aucune séance et ne remplace pas
l'évaluation de l'état réel de l'athlète.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.trajectory.event import (
    EventImpact,
    TrajectoryEvent,
    TrajectoryEventType,
)


@dataclass(frozen=True, slots=True)
class ReturnToTrainingPolicy:
    """Cadre minimal de reprise après un événement."""

    minimum_weeks: int

    reason: str

    requires_clearance: bool = False


def build_return_to_training_policy(
    event: TrajectoryEvent,
) -> ReturnToTrainingPolicy | None:
    """Construit la politique de reprise associée à un événement."""

    duration_days = (
        event.end_date - event.start_date
    ).days + 1

    if event.event_type is TrajectoryEventType.INJURY:
        return _injury_policy(
            event=event,
            duration_days=duration_days,
        )

    if event.event_type is TrajectoryEventType.ILLNESS:
        return _illness_policy(
            event=event,
            duration_days=duration_days,
        )

    if event.event_type is TrajectoryEventType.TRAINING_BREAK:
        return _training_break_policy(
            event=event,
            duration_days=duration_days,
        )

    return None


def _injury_policy(
    *,
    event: TrajectoryEvent,
    duration_days: int,
) -> ReturnToTrainingPolicy:
    if event.impact is EventImpact.LOW:
        minimum_weeks = 1
    elif event.impact is EventImpact.MODERATE:
        minimum_weeks = 2
    else:
        minimum_weeks = 3

    if duration_days > 28:
        minimum_weeks = max(
            minimum_weeks,
            4,
        )

    return ReturnToTrainingPolicy(
        minimum_weeks=minimum_weeks,
        reason="Reprise progressive après blessure.",
        requires_clearance=(
            event.impact
            in {
                EventImpact.HIGH,
                EventImpact.CRITICAL,
            }
        ),
    )


def _illness_policy(
    *,
    event: TrajectoryEvent,
    duration_days: int,
) -> ReturnToTrainingPolicy | None:
    if event.impact is EventImpact.LOW:
        return None

    minimum_weeks = 1

    if (
        event.impact
        in {
            EventImpact.HIGH,
            EventImpact.CRITICAL,
        }
        or duration_days > 7
    ):
        minimum_weeks = 2

    return ReturnToTrainingPolicy(
        minimum_weeks=minimum_weeks,
        reason="Reprise progressive après maladie.",
        requires_clearance=False,
    )


def _training_break_policy(
    *,
    event: TrajectoryEvent,
    duration_days: int,
) -> ReturnToTrainingPolicy | None:
    if duration_days <= 7:
        return None

    if duration_days <= 14:
        minimum_weeks = 1
    elif duration_days <= 28:
        minimum_weeks = 2
    else:
        minimum_weeks = 3

    return ReturnToTrainingPolicy(
        minimum_weeks=minimum_weeks,
        reason="Reconstruction après interruption d'entraînement.",
        requires_clearance=False,
    )
