"""Consolidation de plusieurs adaptations de trajectoire.

Ce module fusionne plusieurs décisions déterministes provenant
de sources différentes : événements, réconciliation de charge,
fatigue ou autres garde-fous.

La décision consolidée conserve toujours l'adaptation la plus
protectrice pour la charge et pour la progression.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.stimulus.training import (
    TrainingModality,
    TrainingStimulus,
)
from opencoach.planning.trajectory.adjustment import (
    AdjustmentSeverity,
    LoadAdjustment,
    ProgressionAdjustment,
    TrajectoryAdjustment,
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


_SEVERITY_ORDER = {
    AdjustmentSeverity.MINOR: 0,
    AdjustmentSeverity.MODERATE: 1,
    AdjustmentSeverity.MAJOR: 2,
}


@dataclass(frozen=True, slots=True)
class ResolvedTrajectoryAdjustment:
    """Décision consolidée issue de plusieurs adaptations."""

    adjustments: tuple[
        TrajectoryAdjustment,
        ...
    ]

    load: LoadAdjustment

    progression: ProgressionAdjustment

    severity: AdjustmentSeverity

    restricted_modalities: tuple[
        TrainingModality,
        ...
    ]

    protected_stimuli: tuple[
        TrainingStimulus,
        ...
    ]

    suppressed_stimuli: tuple[
        TrainingStimulus,
        ...
    ]

    allow_schedule_compression: bool

    requires_return_to_training: bool

    athlete_override_allowed: bool

    reasons: tuple[str, ...]

    notes: tuple[str, ...]


def resolve_trajectory_adjustments(
    *,
    adjustments: tuple[
        TrajectoryAdjustment,
        ...
    ],
) -> ResolvedTrajectoryAdjustment:
    """Consolide plusieurs adaptations de trajectoire."""

    if not adjustments:
        return ResolvedTrajectoryAdjustment(
            adjustments=(),
            load=LoadAdjustment.MAINTAIN,
            progression=ProgressionAdjustment.CONTINUE,
            severity=AdjustmentSeverity.MINOR,
            restricted_modalities=(),
            protected_stimuli=(),
            suppressed_stimuli=(),
            allow_schedule_compression=True,
            requires_return_to_training=False,
            athlete_override_allowed=True,
            reasons=(),
            notes=(),
        )

    load = max(
        (
            adjustment.load
            for adjustment in adjustments
        ),
        key=_LOAD_ORDER.__getitem__,
    )

    progression = max(
        (
            adjustment.progression
            for adjustment in adjustments
        ),
        key=_PROGRESSION_ORDER.__getitem__,
    )

    severity = max(
        (
            adjustment.severity
            for adjustment in adjustments
        ),
        key=_SEVERITY_ORDER.__getitem__,
    )

    restricted_modalities = _unique_modalities(
        adjustment.restricted_modalities
        for adjustment in adjustments
    )

    protected_stimuli = _unique_stimuli(
        adjustment.protected_stimuli
        for adjustment in adjustments
    )

    suppressed_stimuli = _unique_stimuli(
        adjustment.suppressed_stimuli
        for adjustment in adjustments
    )

    overlap = (
        set(protected_stimuli)
        & set(suppressed_stimuli)
    )

    if overlap:
        protected_stimuli = tuple(
            stimulus
            for stimulus in protected_stimuli
            if stimulus not in overlap
        )

    return ResolvedTrajectoryAdjustment(
        adjustments=adjustments,
        load=load,
        progression=progression,
        severity=severity,
        restricted_modalities=restricted_modalities,
        protected_stimuli=protected_stimuli,
        suppressed_stimuli=suppressed_stimuli,
        allow_schedule_compression=all(
            adjustment.allow_schedule_compression
            for adjustment in adjustments
        ),
        requires_return_to_training=any(
            adjustment.requires_return_to_training
            for adjustment in adjustments
        ),
        athlete_override_allowed=all(
            adjustment.athlete_override_allowed
            for adjustment in adjustments
        ),
        reasons=tuple(
            adjustment.reason
            for adjustment in adjustments
        ),
        notes=tuple(
            note
            for adjustment in adjustments
            for note in adjustment.notes
        ),
    )


def _unique_modalities(
    groups,
) -> tuple[
    TrainingModality,
    ...
]:
    result: list[
        TrainingModality
    ] = []

    for group in groups:
        for modality in group:
            if modality not in result:
                result.append(
                    modality
                )

    return tuple(
        result
    )


def _unique_stimuli(
    groups,
) -> tuple[
    TrainingStimulus,
    ...
]:
    result: list[
        TrainingStimulus
    ] = []

    for group in groups:
        for stimulus in group:
            if stimulus not in result:
                result.append(
                    stimulus
                )

    return tuple(
        result
    )
