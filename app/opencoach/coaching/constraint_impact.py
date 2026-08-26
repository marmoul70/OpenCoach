"""Impact coaching des contraintes temporaires de l'athlète.

Ce module distingue explicitement :

- les contraintes logistiques, qui modifient principalement
  les disponibilités ;
- les contraintes physiologiques, qui peuvent imposer
  une réduction structurelle de la charge.

Aucune persistance ni orchestration n'est définie ici.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from opencoach.models import AthleteConstraint


PHYSIOLOGICAL_CONSTRAINT_TYPES = frozenset(
    {
        "illness",
        "injury",
    }
)

LOGISTICAL_CONSTRAINT_TYPES = frozenset(
    {
        "work",
        "travel",
        "family",
        "personal",
        "other",
    }
)


@dataclass(frozen=True, slots=True)
class ConstraintRecoveryImpact:
    """Impact structurel d'une contrainte sur la semaine."""

    requires_weekly_recovery: bool

    prolonged_disruption: bool

    affected_days: int

    reason: str | None = None


def constraint_duration_days(
    constraint: AthleteConstraint,
) -> int:
    """Retourne la durée calendaire inclusive d'une contrainte."""

    return (
        constraint.end_date
        - constraint.start_date
    ).days + 1


def evaluate_constraint_recovery_impact(
    *,
    constraint: AthleteConstraint,
    reference_date: date,
) -> ConstraintRecoveryImpact:
    """Évalue l'impact physiologique d'une contrainte temporaire.

    Les contraintes logistiques ne déclenchent jamais directement
    une semaine de récupération.

    Une maladie ou blessure peut déclencher une réduction structurelle
    lorsque sa durée ou son niveau de restriction dépasse une simple
    perturbation locale.
    """

    affected_days = constraint_duration_days(
        constraint
    )

    if (
        constraint.constraint_type
        not in PHYSIOLOGICAL_CONSTRAINT_TYPES
    ):
        return ConstraintRecoveryImpact(
            requires_weekly_recovery=False,
            prolonged_disruption=False,
            affected_days=affected_days,
        )

    if (
        reference_date < constraint.start_date
        or reference_date > constraint.end_date
    ):
        return ConstraintRecoveryImpact(
            requires_weekly_recovery=False,
            prolonged_disruption=False,
            affected_days=affected_days,
        )

    prolonged = (
        affected_days >= 4
    )

    if (
        constraint.availability
        == "unavailable"
    ):
        return ConstraintRecoveryImpact(
            requires_weekly_recovery=(
                affected_days >= 2
            ),
            prolonged_disruption=prolonged,
            affected_days=affected_days,
            reason=(
                "contrainte physiologique indisponible"
            ),
        )

    if (
        constraint.availability
        == "limited"
    ):
        materially_limited = (
            not constraint.running_allowed
            or (
                constraint.max_duration_minutes
                is not None
                and constraint.max_duration_minutes
                <= 30
            )
        )

        return ConstraintRecoveryImpact(
            requires_weekly_recovery=(
                affected_days >= 2
                and materially_limited
            ),
            prolonged_disruption=(
                prolonged
                and materially_limited
            ),
            affected_days=affected_days,
            reason=(
                "contrainte physiologique limitée"
                if materially_limited
                else None
            ),
        )

    return ConstraintRecoveryImpact(
        requires_weekly_recovery=False,
        prolonged_disruption=False,
        affected_days=affected_days,
    )


def constraints_require_weekly_recovery(
    *,
    constraints: tuple[
        AthleteConstraint,
        ...
    ],
    reference_date: date,
) -> bool:
    """Indique si au moins une contrainte impose une décharge."""

    return any(
        evaluate_constraint_recovery_impact(
            constraint=constraint,
            reference_date=reference_date,
        ).requires_weekly_recovery
        for constraint in constraints
    )


def constraints_have_prolonged_physiological_disruption(
    *,
    constraints: tuple[
        AthleteConstraint,
        ...
    ],
    reference_date: date,
) -> bool:
    """Détecte une maladie/blessure suffisamment longue.

    Ce signal servira ensuite au passage vers RETURN_TO_TRAINING.
    """

    return any(
        evaluate_constraint_recovery_impact(
            constraint=constraint,
            reference_date=reference_date,
        ).prolonged_disruption
        for constraint in constraints
    )


RETURN_TO_TRAINING_LOOKBACK_DAYS = 7


@dataclass(frozen=True, slots=True)
class ConstraintReturnToTrainingImpact:
    """Impact d'une interruption physiologique terminée.

    `requires_return_to_training` indique qu'une maladie ou blessure
    suffisamment longue vient de se terminer et qu'un retour direct
    à la trajectoire normale serait inadapté.
    """

    requires_return_to_training: bool

    disruption_days: int

    days_since_end: int | None

    reason: str | None = None


def evaluate_constraint_return_to_training(
    *,
    constraint: AthleteConstraint,
    reference_date: date,
) -> ConstraintReturnToTrainingImpact:
    """Évalue si une contrainte terminée impose une phase de reprise.

    Seules les contraintes physiologiques sont concernées.

    Une contrainte :
    - encore active ;
    - future ;
    - logistique ;
    - ou trop courte

    ne déclenche pas RETURN_TO_TRAINING.
    """

    disruption_days = constraint_duration_days(
        constraint
    )

    if (
        constraint.constraint_type
        not in PHYSIOLOGICAL_CONSTRAINT_TYPES
    ):
        return ConstraintReturnToTrainingImpact(
            requires_return_to_training=False,
            disruption_days=disruption_days,
            days_since_end=None,
        )

    if reference_date <= constraint.end_date:
        return ConstraintReturnToTrainingImpact(
            requires_return_to_training=False,
            disruption_days=disruption_days,
            days_since_end=None,
        )

    days_since_end = (
        reference_date
        - constraint.end_date
    ).days

    prolonged = (
        disruption_days >= 4
    )

    recent = (
        days_since_end
        <= RETURN_TO_TRAINING_LOOKBACK_DAYS
    )

    requires_return = (
        prolonged
        and recent
    )

    return ConstraintReturnToTrainingImpact(
        requires_return_to_training=(
            requires_return
        ),
        disruption_days=(
            disruption_days
        ),
        days_since_end=(
            days_since_end
        ),
        reason=(
            "reprise après interruption physiologique prolongée"
            if requires_return
            else None
        ),
    )


def constraints_require_return_to_training(
    *,
    constraints: tuple[
        AthleteConstraint,
        ...
    ],
    reference_date: date,
) -> bool:
    """Détecte une reprise après maladie/blessure prolongée."""

    return any(
        evaluate_constraint_return_to_training(
            constraint=constraint,
            reference_date=reference_date,
        ).requires_return_to_training
        for constraint in constraints
    )
