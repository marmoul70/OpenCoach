"""Analyse déterministe d'un historique de réconciliations de charge.

Ce module observe plusieurs semaines réalisées afin de détecter une dérive
durable entre la trajectoire théorique et la charge réellement effectuée.

Il ne remplace pas la politique hebdomadaire :
- weekly_load_reconciliation mesure un écart ponctuel ;
- weekly_load_reconciliation_policy protège la semaine suivante ;
- ce module décide si la référence structurelle doit être réancrée.

Les données incomplètes sont exclues des décisions automatiques.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .weekly_load_reconciliation import (
    LoadReconciliationStatus,
)
from .weekly_load_reconciliation_context import (
    ContextualWeeklyLoadReconciliation,
    LoadDeviationCause,
)


class ReconciliationTrendStatus(StrEnum):
    """État de la dérive observée sur plusieurs semaines."""

    STABLE = "stable"
    WATCH = "watch"
    REANCHOR = "reanchor"


@dataclass(frozen=True, slots=True)
class ReconciliationHistoryPolicy:
    """Politique de détection et de réancrage."""

    watch_consecutive_weeks: int = 2
    reanchor_consecutive_weeks: int = 3

    minimum_reanchor_deficit: float = 0.20
    reanchor_strength: float = 0.50

    def __post_init__(self) -> None:
        if self.watch_consecutive_weeks < 1:
            raise ValueError(
                "Le seuil de surveillance doit être positif."
            )

        if (
            self.reanchor_consecutive_weeks
            < self.watch_consecutive_weeks
        ):
            raise ValueError(
                "Le seuil de réancrage ne peut pas être inférieur "
                "au seuil de surveillance."
            )

        if not 0.0 <= self.minimum_reanchor_deficit <= 1.0:
            raise ValueError(
                "Le déficit minimal de réancrage doit être compris "
                "entre 0 et 1."
            )

        if not 0.0 <= self.reanchor_strength <= 1.0:
            raise ValueError(
                "La force de réancrage doit être comprise entre 0 et 1."
            )


@dataclass(frozen=True, slots=True)
class ReconciliationTrend:
    """Synthèse d'un historique récent de charge."""

    status: ReconciliationTrendStatus

    considered_weeks: int
    consecutive_under_target_weeks: int

    average_relative_delta: float

    current_reference_load: float
    observed_load_reference: float
    recommended_reference_load: float

    reanchoring_applied: bool

    reasons: tuple[str, ...]


DEFAULT_RECONCILIATION_HISTORY_POLICY = (
    ReconciliationHistoryPolicy()
)


def analyze_reconciliation_history(
    *,
    history: tuple[
        ContextualWeeklyLoadReconciliation,
        ...
    ],
    current_reference_load: float,
    policy: ReconciliationHistoryPolicy = (
        DEFAULT_RECONCILIATION_HISTORY_POLICY
    ),
) -> ReconciliationTrend:
    """Analyse les semaines récentes et propose éventuellement un réancrage."""

    if current_reference_load < 0:
        raise ValueError(
            "La charge de référence ne peut pas être négative."
        )

    usable_history = tuple(
        item
        for item in history
        if (
            item.cause
            is not LoadDeviationCause.INCOMPLETE_DATA
        )
    )

    if not usable_history:
        return _stable_result(
            current_reference_load=current_reference_load,
            reason=(
                "Aucune semaine exploitable pour analyser "
                "la dérive de trajectoire."
            ),
        )

    consecutive_under_target = (
        _count_recent_under_target_weeks(
            usable_history
        )
    )

    relevant_history = (
        usable_history[
            -consecutive_under_target:
        ]
        if consecutive_under_target > 0
        else ()
    )

    if not relevant_history:
        return _stable_result(
            current_reference_load=current_reference_load,
            reason=(
                "La semaine la plus récente ne présente pas "
                "de sous-charge significative."
            ),
        )

    average_relative_delta = sum(
        item.reconciliation.relative_delta
        for item in relevant_history
    ) / len(relevant_history)

    observed_load_reference = sum(
        item.reconciliation.actual_load
        for item in relevant_history
    ) / len(relevant_history)

    if (
        consecutive_under_target
        < policy.watch_consecutive_weeks
    ):
        return ReconciliationTrend(
            status=ReconciliationTrendStatus.STABLE,
            considered_weeks=len(relevant_history),
            consecutive_under_target_weeks=(
                consecutive_under_target
            ),
            average_relative_delta=average_relative_delta,
            current_reference_load=current_reference_load,
            observed_load_reference=observed_load_reference,
            recommended_reference_load=current_reference_load,
            reanchoring_applied=False,
            reasons=(
                "Sous-charge ponctuelle : la référence structurelle "
                "est conservée.",
            ),
        )

    if (
        consecutive_under_target
        < policy.reanchor_consecutive_weeks
    ):
        return ReconciliationTrend(
            status=ReconciliationTrendStatus.WATCH,
            considered_weeks=len(relevant_history),
            consecutive_under_target_weeks=(
                consecutive_under_target
            ),
            average_relative_delta=average_relative_delta,
            current_reference_load=current_reference_load,
            observed_load_reference=observed_load_reference,
            recommended_reference_load=current_reference_load,
            reanchoring_applied=False,
            reasons=(
                "Sous-charge répétée : la trajectoire doit être "
                "surveillée avant réancrage.",
            ),
        )

    deficit = max(
        0.0,
        -average_relative_delta,
    )

    if deficit < policy.minimum_reanchor_deficit:
        return ReconciliationTrend(
            status=ReconciliationTrendStatus.WATCH,
            considered_weeks=len(relevant_history),
            consecutive_under_target_weeks=(
                consecutive_under_target
            ),
            average_relative_delta=average_relative_delta,
            current_reference_load=current_reference_load,
            observed_load_reference=observed_load_reference,
            recommended_reference_load=current_reference_load,
            reanchoring_applied=False,
            reasons=(
                "Sous-charge répétée mais déficit cumulé encore "
                "insuffisant pour réancrer la référence.",
            ),
        )

    recommended_reference_load = (
        current_reference_load
        + (
            observed_load_reference
            - current_reference_load
        )
        * policy.reanchor_strength
    )

    recommended_reference_load = max(
        0.0,
        recommended_reference_load,
    )

    return ReconciliationTrend(
        status=ReconciliationTrendStatus.REANCHOR,
        considered_weeks=len(relevant_history),
        consecutive_under_target_weeks=(
            consecutive_under_target
        ),
        average_relative_delta=average_relative_delta,
        current_reference_load=current_reference_load,
        observed_load_reference=observed_load_reference,
        recommended_reference_load=(
            recommended_reference_load
        ),
        reanchoring_applied=True,
        reasons=(
            "Sous-charge durable détectée : la référence est "
            "réancrée progressivement vers la charge réellement "
            "effectuée.",
        ),
    )


def _count_recent_under_target_weeks(
    history: tuple[
        ContextualWeeklyLoadReconciliation,
        ...
    ],
) -> int:
    """Compte les sous-charges significatives consécutives les plus récentes."""

    count = 0

    for item in reversed(history):
        if item.reconciliation.status not in {
            LoadReconciliationStatus.UNDER_TARGET,
            LoadReconciliationStatus.STRONGLY_UNDER_TARGET,
        }:
            break

        count += 1

    return count


def _stable_result(
    *,
    current_reference_load: float,
    reason: str,
) -> ReconciliationTrend:
    """Construit une synthèse neutre."""

    return ReconciliationTrend(
        status=ReconciliationTrendStatus.STABLE,
        considered_weeks=0,
        consecutive_under_target_weeks=0,
        average_relative_delta=0.0,
        current_reference_load=current_reference_load,
        observed_load_reference=current_reference_load,
        recommended_reference_load=current_reference_load,
        reanchoring_applied=False,
        reasons=(reason,),
    )
