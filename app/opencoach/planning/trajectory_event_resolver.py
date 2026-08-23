"""Résolution des événements de trajectoire.

Ce module agrège les adaptations produites par plusieurs événements
afin de fournir une décision déterministe unique au moteur hebdomadaire.
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
from .trajectory_event import (
    TrajectoryEvent,
)


_LOAD_ORDER = {
    LoadAdjustment.MAINTAIN: 0,
    LoadAdjustment.REDUCE_SLIGHTLY: 1,
    LoadAdjustment.REDUCE: 2,
    LoadAdjustment.REDUCE_STRONGLY: 3,
    LoadAdjustment.SUSPEND: 4,
}


_PROGRESSION_ORDER = {
    ProgressionAdjustment.CONTINUE: 0,
    ProgressionAdjustment.SLOW: 1,
    ProgressionAdjustment.PAUSE: 2,
    ProgressionAdjustment.REBUILD: 3,
}


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

    if not adjustments:
        return ResolvedTrajectoryEvents(
            adjustments=(),
            load_adjustment=LoadAdjustment.MAINTAIN,
            progression_adjustment=(
                ProgressionAdjustment.CONTINUE
            ),
            event_requires_recovery=False,
            requires_return_to_training=False,
            allow_schedule_compression=True,
            athlete_schedule_constrained=False,
            notes=(),
        )

    load_adjustment = max(
        (
            adjustment.load
            for adjustment in adjustments
        ),
        key=_LOAD_ORDER.__getitem__,
    )

    progression_adjustment = max(
        (
            adjustment.progression
            for adjustment in adjustments
        ),
        key=_PROGRESSION_ORDER.__getitem__,
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

    requires_return_to_training = any(
        adjustment.requires_return_to_training
        for adjustment in adjustments
    )

    allow_schedule_compression = all(
        adjustment.allow_schedule_compression
        for adjustment in adjustments
    )

    athlete_schedule_constrained = any(
        event.athlete_imposed
        for event in events
    )

    notes = tuple(
        note
        for adjustment in adjustments
        for note in adjustment.notes
    )

    return ResolvedTrajectoryEvents(
        adjustments=adjustments,
        load_adjustment=load_adjustment,
        progression_adjustment=progression_adjustment,
        event_requires_recovery=event_requires_recovery,
        requires_return_to_training=requires_return_to_training,
        allow_schedule_compression=allow_schedule_compression,
        athlete_schedule_constrained=athlete_schedule_constrained,
        notes=notes,
    )
