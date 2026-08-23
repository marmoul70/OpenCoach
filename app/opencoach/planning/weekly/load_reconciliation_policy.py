"""Politique d'adaptation après réconciliation de charge hebdomadaire.

Ce module transforme un écart contextualisé entre charge planifiée
et charge réalisée en recommandation de trajectoire.

Il réutilise volontairement TrajectoryAdjustment afin de conserver
une seule représentation métier des adaptations dans OpenCoach.

Cette politique ne génère aucune séance et ne remplace pas les
événements explicites de trajectoire pour les blessures, maladies
ou interruptions significatives.
"""

from __future__ import annotations

from opencoach.planning.trajectory.adjustment import (
    AdjustmentSeverity,
    LoadAdjustment,
    ProgressionAdjustment,
    TrajectoryAdjustment,
)
from opencoach.planning.weekly.load_reconciliation import (
    LoadReconciliationStatus,
)
from opencoach.planning.weekly.load_reconciliation_context import (
    ContextualWeeklyLoadReconciliation,
    LoadDeviationCause,
)


def build_reconciliation_adjustment(
    context: ContextualWeeklyLoadReconciliation,
) -> TrajectoryAdjustment:
    """Construit l'adaptation recommandée après une semaine réalisée."""

    status = context.reconciliation.status
    cause = context.cause

    if status is LoadReconciliationStatus.ON_TARGET:
        return _continue_adjustment(
            reason="Charge hebdomadaire conforme à la trajectoire.",
        )

    if cause in {
        LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        LoadDeviationCause.PERSONAL_CONSTRAINT,
        LoadDeviationCause.ATHLETE_CHOICE,
    }:
        return _athlete_context_adjustment(
            context=context,
        )

    if cause is LoadDeviationCause.INCOMPLETE_DATA:
        return _continue_adjustment(
            reason=(
                "Données hebdomadaires incomplètes : "
                "aucune correction automatique de trajectoire."
            ),
        )

    if cause is LoadDeviationCause.FATIGUE:
        return _fatigue_adjustment(
            status=status,
        )

    if cause is LoadDeviationCause.ILLNESS:
        return _illness_adjustment(
            status=status,
        )

    if cause is LoadDeviationCause.INJURY:
        return _injury_adjustment(
            status=status,
        )

    if _is_over_target(status):
        return _overload_adjustment(
            status=status,
            cause=cause,
        )

    if cause is LoadDeviationCause.SPORT_EVENT:
        return _continue_adjustment(
            reason=(
                "Écart lié à un événement sportif : "
                "la trajectoire événementielle reste prioritaire."
            ),
        )

    return _unknown_underload_adjustment(
        status=status,
    )


def _athlete_context_adjustment(
    *,
    context: ContextualWeeklyLoadReconciliation,
) -> TrajectoryAdjustment:
    """Préserve la trajectoire lors d'un choix ou d'une contrainte externe."""

    cause = context.cause

    labels = {
        LoadDeviationCause.PROFESSIONAL_CONSTRAINT: (
            "contrainte professionnelle"
        ),
        LoadDeviationCause.PERSONAL_CONSTRAINT: (
            "contrainte personnelle"
        ),
        LoadDeviationCause.ATHLETE_CHOICE: (
            "choix explicite de l'athlète"
        ),
    }

    return TrajectoryAdjustment(
        reason=(
            f"Écart lié à une {labels[cause]} : "
            "la trajectoire n'est pas corrigée automatiquement."
        ),
        severity=AdjustmentSeverity.MINOR,
        load=LoadAdjustment.MAINTAIN,
        progression=ProgressionAdjustment.CONTINUE,
        allow_schedule_compression=True,
        athlete_override_allowed=True,
        notes=(
            "L'athlète conserve la décision finale.",
        ),
    )


def _fatigue_adjustment(
    *,
    status: LoadReconciliationStatus,
) -> TrajectoryAdjustment:
    """Adapte la trajectoire lorsqu'une sous-charge reflète la fatigue."""

    if _is_over_target(status):
        return _overload_adjustment(
            status=status,
            cause=LoadDeviationCause.FATIGUE,
        )

    if status is LoadReconciliationStatus.STRONGLY_UNDER_TARGET:
        return TrajectoryAdjustment(
            reason=(
                "Forte sous-charge associée à de la fatigue."
            ),
            severity=AdjustmentSeverity.MODERATE,
            load=LoadAdjustment.REDUCE,
            progression=ProgressionAdjustment.PAUSE,
            allow_schedule_compression=False,
            athlete_override_allowed=True,
        )

    return TrajectoryAdjustment(
        reason="Sous-charge associée à de la fatigue.",
        severity=AdjustmentSeverity.MINOR,
        load=LoadAdjustment.REDUCE_SLIGHTLY,
        progression=ProgressionAdjustment.SLOW,
        allow_schedule_compression=False,
        athlete_override_allowed=True,
    )


def _illness_adjustment(
    *,
    status: LoadReconciliationStatus,
) -> TrajectoryAdjustment:
    """Adapte prudemment la trajectoire en présence de maladie."""

    if _is_over_target(status):
        return TrajectoryAdjustment(
            reason=(
                "Charge supérieure à la cible malgré une maladie."
            ),
            severity=AdjustmentSeverity.MAJOR,
            load=LoadAdjustment.REDUCE_STRONGLY,
            progression=ProgressionAdjustment.PAUSE,
            allow_schedule_compression=False,
            athlete_override_allowed=True,
        )

    if status is LoadReconciliationStatus.STRONGLY_UNDER_TARGET:
        load = LoadAdjustment.REDUCE_STRONGLY
        severity = AdjustmentSeverity.MAJOR
    else:
        load = LoadAdjustment.REDUCE
        severity = AdjustmentSeverity.MODERATE

    return TrajectoryAdjustment(
        reason="Sous-charge associée à une maladie.",
        severity=severity,
        load=load,
        progression=ProgressionAdjustment.PAUSE,
        allow_schedule_compression=False,
        athlete_override_allowed=True,
        notes=(
            "Un événement maladie explicite peut imposer "
            "une politique de retour à l'entraînement.",
        ),
    )


def _injury_adjustment(
    *,
    status: LoadReconciliationStatus,
) -> TrajectoryAdjustment:
    """Protège la trajectoire lorsqu'une blessure explique l'écart."""

    if status is LoadReconciliationStatus.STRONGLY_UNDER_TARGET:
        return TrajectoryAdjustment(
            reason=(
                "Forte sous-charge associée à une blessure."
            ),
            severity=AdjustmentSeverity.MAJOR,
            load=LoadAdjustment.SUSPEND,
            progression=ProgressionAdjustment.REBUILD,
            allow_schedule_compression=False,
            requires_return_to_training=True,
            athlete_override_allowed=True,
            notes=(
                "La reprise doit être évaluée avant reconstruction.",
            ),
        )

    return TrajectoryAdjustment(
        reason="Écart de charge associé à une blessure.",
        severity=AdjustmentSeverity.MAJOR,
        load=LoadAdjustment.REDUCE_STRONGLY,
        progression=ProgressionAdjustment.PAUSE,
        allow_schedule_compression=False,
        athlete_override_allowed=True,
        notes=(
            "Un événement blessure explicite reste nécessaire "
            "pour piloter le cycle complet de reprise.",
        ),
    )


def _overload_adjustment(
    *,
    status: LoadReconciliationStatus,
    cause: LoadDeviationCause,
) -> TrajectoryAdjustment:
    """Protège la semaine suivante après dépassement de charge."""

    if status is LoadReconciliationStatus.STRONGLY_OVER_TARGET:
        return TrajectoryAdjustment(
            reason=(
                "Charge réalisée fortement supérieure à la cible."
            ),
            severity=AdjustmentSeverity.MODERATE,
            load=LoadAdjustment.REDUCE,
            progression=ProgressionAdjustment.SLOW,
            allow_schedule_compression=False,
            athlete_override_allowed=True,
            notes=(
                f"Cause déclarée : {cause.value}.",
            ),
        )

    return TrajectoryAdjustment(
        reason="Charge réalisée supérieure à la cible.",
        severity=AdjustmentSeverity.MINOR,
        load=LoadAdjustment.REDUCE_SLIGHTLY,
        progression=ProgressionAdjustment.CONTINUE,
        allow_schedule_compression=False,
        athlete_override_allowed=True,
        notes=(
            f"Cause déclarée : {cause.value}.",
        ),
    )


def _unknown_underload_adjustment(
    *,
    status: LoadReconciliationStatus,
) -> TrajectoryAdjustment:
    """Applique une correction prudente lorsque la cause reste inconnue."""

    if status is LoadReconciliationStatus.STRONGLY_UNDER_TARGET:
        return TrajectoryAdjustment(
            reason=(
                "Forte sous-charge sans cause suffisamment établie."
            ),
            severity=AdjustmentSeverity.MODERATE,
            load=LoadAdjustment.REDUCE_SLIGHTLY,
            progression=ProgressionAdjustment.SLOW,
            allow_schedule_compression=True,
            athlete_override_allowed=True,
        )

    return _continue_adjustment(
        reason=(
            "Sous-charge modérée sans cause suffisamment établie."
        ),
    )


def _continue_adjustment(
    *,
    reason: str,
) -> TrajectoryAdjustment:
    """Construit une décision neutre de poursuite."""

    return TrajectoryAdjustment(
        reason=reason,
        severity=AdjustmentSeverity.MINOR,
        load=LoadAdjustment.MAINTAIN,
        progression=ProgressionAdjustment.CONTINUE,
        allow_schedule_compression=True,
        athlete_override_allowed=True,
    )


def _is_over_target(
    status: LoadReconciliationStatus,
) -> bool:
    return status in {
        LoadReconciliationStatus.OVER_TARGET,
        LoadReconciliationStatus.STRONGLY_OVER_TARGET,
    }
