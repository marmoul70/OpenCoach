"""Gestion adaptative des cycles de charge et de récupération.

Ce module décide si une semaine doit poursuivre la progression normale
ou devenir une semaine de décharge.

Il ne génère aucune séance et ne choisit aucune modalité sportive.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


class RecoveryTrigger(StrEnum):
    """Raison ayant déclenché une semaine de récupération."""

    NONE = "none"
    PLANNED = "planned"
    FATIGUE = "fatigue"
    EVENT = "event"
    PHASE_TRANSITION = "phase_transition"


@dataclass(frozen=True, slots=True)
class LoadRecoveryPolicy:
    """Politique de récupération associée à une phase."""

    phase: TrainingPhase

    preferred_loading_weeks: int
    recovery_factor: float

    def __post_init__(self) -> None:
        if self.preferred_loading_weeks < 1:
            raise ValueError(
                "Le nombre de semaines de charge doit être positif."
            )

        if not 0.0 < self.recovery_factor <= 1.0:
            raise ValueError(
                "Le facteur de récupération doit être compris "
                "entre 0 et 1."
            )


@dataclass(frozen=True, slots=True)
class LoadRecoveryDecision:
    """Décision du moteur concernant la semaine à venir."""

    recovery_week: bool

    trigger: RecoveryTrigger

    load_factor: float

    loading_weeks_since_recovery: int

    def __post_init__(self) -> None:
        if not 0.0 <= self.load_factor <= 1.0:
            raise ValueError(
                "Le facteur de charge doit être compris entre 0 et 1."
            )

        if self.loading_weeks_since_recovery < 0:
            raise ValueError(
                "Le nombre de semaines depuis la récupération "
                "ne peut pas être négatif."
            )

        if (
            self.recovery_week
            and self.trigger is RecoveryTrigger.NONE
        ):
            raise ValueError(
                "Une semaine de récupération doit avoir "
                "un déclencheur."
            )


DEFAULT_RECOVERY_POLICIES = {
    TrainingPhase.FOUNDATION: LoadRecoveryPolicy(
        phase=TrainingPhase.FOUNDATION,
        preferred_loading_weeks=3,
        recovery_factor=0.80,
    ),
    TrainingPhase.BASE: LoadRecoveryPolicy(
        phase=TrainingPhase.BASE,
        preferred_loading_weeks=3,
        recovery_factor=0.80,
    ),
    TrainingPhase.BUILD: LoadRecoveryPolicy(
        phase=TrainingPhase.BUILD,
        preferred_loading_weeks=3,
        recovery_factor=0.75,
    ),
    TrainingPhase.SPECIFIC: LoadRecoveryPolicy(
        phase=TrainingPhase.SPECIFIC,
        preferred_loading_weeks=2,
        recovery_factor=0.80,
    ),
    TrainingPhase.RETURN_TO_TRAINING: LoadRecoveryPolicy(
        phase=TrainingPhase.RETURN_TO_TRAINING,
        preferred_loading_weeks=2,
        recovery_factor=0.85,
    ),
}


def decide_load_recovery(
    *,
    phase: TrainingPhase,
    loading_weeks_since_recovery: int,
    fatigue_requires_recovery: bool = False,
    event_requires_recovery: bool = False,
    phase_transition_requires_recovery: bool = False,
    policies: dict[
        TrainingPhase,
        LoadRecoveryPolicy,
    ] = DEFAULT_RECOVERY_POLICIES,
) -> LoadRecoveryDecision:
    """Décide si la semaine suivante doit être une décharge."""

    if loading_weeks_since_recovery < 0:
        raise ValueError(
            "Le nombre de semaines depuis la récupération "
            "ne peut pas être négatif."
        )

    if phase in {
        TrainingPhase.RECOVERY,
        TrainingPhase.TAPER,
    }:
        return LoadRecoveryDecision(
            recovery_week=False,
            trigger=RecoveryTrigger.NONE,
            load_factor=1.0,
            loading_weeks_since_recovery=(
                loading_weeks_since_recovery
            ),
        )

    try:
        policy = policies[phase]
    except KeyError as exc:
        raise ValueError(
            f"Aucune politique de récupération pour la phase {phase}."
        ) from exc

    if fatigue_requires_recovery:
        trigger = RecoveryTrigger.FATIGUE

    elif event_requires_recovery:
        trigger = RecoveryTrigger.EVENT

    elif phase_transition_requires_recovery:
        trigger = RecoveryTrigger.PHASE_TRANSITION

    elif (
        loading_weeks_since_recovery
        >= policy.preferred_loading_weeks
    ):
        trigger = RecoveryTrigger.PLANNED

    else:
        return LoadRecoveryDecision(
            recovery_week=False,
            trigger=RecoveryTrigger.NONE,
            load_factor=1.0,
            loading_weeks_since_recovery=(
                loading_weeks_since_recovery
            ),
        )

    return LoadRecoveryDecision(
        recovery_week=True,
        trigger=trigger,
        load_factor=policy.recovery_factor,
        loading_weeks_since_recovery=0,
    )
