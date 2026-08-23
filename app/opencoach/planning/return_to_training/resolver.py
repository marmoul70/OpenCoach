"""Résolution du retour à l'entraînement à partir des événements.

Ce module détermine si, à une date donnée, l'athlète se trouve
dans une période minimale de reprise après un événement terminé.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from opencoach.planning.return_to_training.policy import (
    ReturnToTrainingPolicy,
    build_return_to_training_policy,
)
from opencoach.planning.return_to_training.state import (
    ReturnToTrainingState,
    calculate_return_to_training_state,
)
from opencoach.planning.trajectory.event import (
    TrajectoryEvent,
)
from enum import StrEnum

from opencoach.planning.return_to_training.clearance import (
    ReturnToTrainingClearance,
    ReturnToTrainingReadiness,
    evaluate_return_to_training_clearance,
)

class ReturnToTrainingStatus(StrEnum):
    """État du processus de retour à l'entraînement."""

    NONE = "none"
    MINIMUM_ACTIVE = "minimum_active"
    AWAITING_CLEARANCE = "awaiting_clearance"
    CLEARED = "cleared"

@dataclass(frozen=True, slots=True)
class ResolvedReturnToTraining:
    """Décision consolidée de retour à l'entraînement."""

    status: ReturnToTrainingStatus

    source_event: TrajectoryEvent | None = None

    policy: ReturnToTrainingPolicy | None = None

    state: ReturnToTrainingState | None = None

    clearance: ReturnToTrainingClearance | None = None

    @property
    def active(self) -> bool:
        """Indique si RETURN_TO_TRAINING doit rester effectif."""

        return self.status in {
            ReturnToTrainingStatus.MINIMUM_ACTIVE,
            ReturnToTrainingStatus.AWAITING_CLEARANCE,
        }

def resolve_return_to_training(
    *,
    planning_date: date,
    events: tuple[
        TrajectoryEvent,
        ...
    ],
    readiness: ReturnToTrainingReadiness | None = None,
) -> ResolvedReturnToTraining:
    """Résout l'état de reprise applicable à la date demandée."""

    candidates: list[
        tuple[
            TrajectoryEvent,
            ReturnToTrainingPolicy,
            ReturnToTrainingState,
        ]
    ] = []

    for event in events:
        if event.end_date >= planning_date:
            continue

        policy = build_return_to_training_policy(
            event
        )

        if policy is None:
            continue

        state = calculate_return_to_training_state(
            planning_date=planning_date,
            event_end_date=event.end_date,
            policy=policy,
        )

        candidates.append(
            (
                event,
                policy,
                state,
            )
        )

    if not candidates:
        return ResolvedReturnToTraining(
            status=ReturnToTrainingStatus.NONE,
        )

    event, policy, state = max(
        candidates,
        key=lambda candidate: (
            candidate[0].end_date
        ),
    )

    if state.active:
        return ResolvedReturnToTraining(
            status=(
                ReturnToTrainingStatus.MINIMUM_ACTIVE
            ),
            source_event=event,
            policy=policy,
            state=state,
        )

    effective_readiness = (
        readiness
        if readiness is not None
        else ReturnToTrainingReadiness()
    )

    clearance = evaluate_return_to_training_clearance(
        minimum_completed=state.minimum_completed,
        requires_clearance=policy.requires_clearance,
        readiness=effective_readiness,
    )

    status = (
        ReturnToTrainingStatus.CLEARED
        if clearance.allowed
        else ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    return ResolvedReturnToTraining(
        status=status,
        source_event=event,
        policy=policy,
        state=state,
        clearance=clearance,
    )