"""Résolution des événements de trajectoire.

Ce module transforme les événements actifs en adaptations métier,
puis utilise le resolver commun pour produire une décision
déterministe consolidée.

Il ne contient volontairement aucune règle concurrente de priorité
entre les adaptations.
"""

from __future__ import annotations

from dataclasses import dataclass

from .coaching_trajectory_engine import (
    CoachingTrajectoryEngine,
)
from .trajectory_adjustment import (
    LoadAdjustment,
    ProgressionAdjustment,
    TrajectoryAdjustment,
)
from .trajectory_adjustment_resolver import (
    resolve_trajectory_adjustments,
)
from .trajectory_event import (
    TrajectoryEvent,
)


@dataclass(frozen=True, slots=True)
class ResolvedTrajectoryEvents:
    """Décision consolidée issue des événements actifs."""

    adjustments: tuple[
        TrajectoryAdjustment,
        ...
    ]

    load_adjustment: LoadAdjustment

    progression_adjustment: ProgressionAdjustment

    event_requires_recovery: bool

    requires_return_to_training: bool

    allow_schedule_compression: bool

    athlete_schedule_constrained: bool

    notes: tuple[str, ...]


def resolve_trajectory_events(
    *,
    events: tuple[
        TrajectoryEvent,
        ...
    ],
    engine: CoachingTrajectoryEngine | None = None,
) -> ResolvedTrajectoryEvents:
    """Agrège les impacts de tous les événements actifs."""

    trajectory_engine = (
        engine
        if engine is not None
        else CoachingTrajectoryEngine()
    )

    adjustments = tuple(
        trajectory_engine.adjust_for_event(
            event
        )
        for event in events
    )

    resolved = resolve_trajectory_adjustments(
        adjustments=adjustments,
    )

    event_requires_recovery = any(
        adjustment.load
        in {
            LoadAdjustment.REDUCE,
            LoadAdjustment.REDUCE_STRONGLY,
            LoadAdjustment.SUSPEND,
        }
        for adjustment in adjustments
    )

    athlete_schedule_constrained = any(
        event.athlete_imposed
        for event in events
    )

    return ResolvedTrajectoryEvents(
        adjustments=adjustments,
        load_adjustment=resolved.load,
        progression_adjustment=resolved.progression,
        event_requires_recovery=event_requires_recovery,
        requires_return_to_training=(
            resolved.requires_return_to_training
        ),
        allow_schedule_compression=(
            resolved.allow_schedule_compression
        ),
        athlete_schedule_constrained=(
            athlete_schedule_constrained
        ),
        notes=resolved.notes,
    )