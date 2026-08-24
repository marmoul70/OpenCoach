"""Progression déterministe du volume hebdomadaire OpenCoach.

Ce module calcule une cible de durée hebdomadaire.

Il ne choisit ni les séances, ni leur placement, ni leur contenu.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


@dataclass(frozen=True, slots=True)
class VolumeProgressionPolicy:
    """Politique de progression temporelle associée à une phase."""

    phase: TrainingPhase

    progression_rate: float

    def __post_init__(self) -> None:
        if self.progression_rate < -1.0:
            raise ValueError(
                "Le taux de progression du volume "
                "ne peut pas être inférieur à -100 %."
            )


@dataclass(frozen=True, slots=True)
class WeeklyVolumeTarget:
    """Cible temporelle hebdomadaire calculée par le moteur."""

    previous_duration_minutes: float

    theoretical_duration_minutes: float
    target_duration_minutes: float

    phase: TrainingPhase

    progression_limited: bool = False

    goal_demand_minutes: float | None = None

    reachable_duration_ceiling_minutes: (
        float | None
    ) = None

    goal_demand_reachable: bool | None = None

    def __post_init__(self) -> None:
        values = (
            self.previous_duration_minutes,
            self.theoretical_duration_minutes,
            self.target_duration_minutes,
        )

        if any(
            value < 0
            for value in values
        ):
            raise ValueError(
                "Les durées hebdomadaires "
                "ne peuvent pas être négatives."
            )

        if (
            self.goal_demand_minutes is not None
            and self.goal_demand_minutes < 0
        ):
            raise ValueError(
                "La demande de volume "
                "ne peut pas être négative."
            )

        if (
            self.reachable_duration_ceiling_minutes
            is not None
            and self.reachable_duration_ceiling_minutes < 0
        ):
            raise ValueError(
                "Le plafond de volume atteignable "
                "ne peut pas être négatif."
            )


DEFAULT_VOLUME_POLICIES = {
    TrainingPhase.FOUNDATION: VolumeProgressionPolicy(
        phase=TrainingPhase.FOUNDATION,
        progression_rate=0.03,
    ),
    TrainingPhase.BASE: VolumeProgressionPolicy(
        phase=TrainingPhase.BASE,
        progression_rate=0.04,
    ),
    TrainingPhase.BUILD: VolumeProgressionPolicy(
        phase=TrainingPhase.BUILD,
        progression_rate=0.06,
    ),
    TrainingPhase.SPECIFIC: VolumeProgressionPolicy(
        phase=TrainingPhase.SPECIFIC,
        progression_rate=0.04,
    ),
    TrainingPhase.TAPER: VolumeProgressionPolicy(
        phase=TrainingPhase.TAPER,
        progression_rate=-0.25,
    ),
    TrainingPhase.RECOVERY: VolumeProgressionPolicy(
        phase=TrainingPhase.RECOVERY,
        progression_rate=-0.25,
    ),
    TrainingPhase.RETURN_TO_TRAINING: VolumeProgressionPolicy(
        phase=TrainingPhase.RETURN_TO_TRAINING,
        progression_rate=-0.15,
    ),
}


def calculate_weekly_volume_target(
    *,
    previous_duration_minutes: float,
    phase: TrainingPhase,
    maximum_progression_rate: float = 0.10,
    goal_demand_minutes: float | None = None,
    weeks_remaining: int | None = None,
    policies: dict[
        TrainingPhase,
        VolumeProgressionPolicy,
    ] = DEFAULT_VOLUME_POLICIES,
) -> WeeklyVolumeTarget:
    """Calcule la cible de volume de la semaine suivante."""

    if previous_duration_minutes < 0:
        raise ValueError(
            "La durée hebdomadaire précédente "
            "ne peut pas être négative."
        )

    if maximum_progression_rate < 0:
        raise ValueError(
            "Le taux maximal de progression "
            "ne peut pas être négatif."
        )

    if (
        goal_demand_minutes is not None
        and goal_demand_minutes < 0
    ):
        raise ValueError(
            "La demande de volume "
            "ne peut pas être négative."
        )

    if (
        weeks_remaining is not None
        and weeks_remaining < 0
    ):
        raise ValueError(
            "Le nombre de semaines restantes "
            "ne peut pas être négatif."
        )

    if (
        goal_demand_minutes is not None
        and weeks_remaining is None
    ):
        raise ValueError(
            "Le nombre de semaines restantes "
            "est requis pour évaluer "
            "la demande de volume."
        )

    try:
        policy = policies[
            phase
        ]
    except KeyError as exc:
        raise ValueError(
            "Aucune politique de volume "
            f"pour la phase {phase}."
        ) from exc

    theoretical_progression_rate = (
        policy.progression_rate
    )

    if (
        goal_demand_minutes is not None
        and weeks_remaining is not None
        and previous_duration_minutes > 0
        and goal_demand_minutes
        > previous_duration_minutes
        and policy.progression_rate >= 0
    ):
        progression_steps = (
            weeks_remaining
            + 1
        )

        required_progression_rate = (
            (
                goal_demand_minutes
                / previous_duration_minutes
            )
            ** (
                1.0
                / progression_steps
            )
            - 1.0
        )

        theoretical_progression_rate = max(
            theoretical_progression_rate,
            required_progression_rate,
        )

    theoretical_duration_minutes = max(
        0.0,
        previous_duration_minutes
        * (
            1.0
            + theoretical_progression_rate
        ),
    )

    effective_progression_rate = (
        theoretical_progression_rate
    )

    progression_limited = False

    if (
        effective_progression_rate > 0
        and effective_progression_rate
        > maximum_progression_rate
    ):
        effective_progression_rate = (
            maximum_progression_rate
        )

        progression_limited = True

    target_duration_minutes = max(
        0.0,
        previous_duration_minutes
        * (
            1.0
            + effective_progression_rate
        ),
    )

    if goal_demand_minutes is not None:
        target_duration_minutes = min(
            target_duration_minutes,
            goal_demand_minutes,
        )

    (
        reachable_duration_ceiling_minutes,
        goal_demand_reachable,
    ) = _resolve_goal_reachability(
        previous_duration_minutes=(
            previous_duration_minutes
        ),
        maximum_progression_rate=(
            maximum_progression_rate
        ),
        goal_demand_minutes=(
            goal_demand_minutes
        ),
        weeks_remaining=weeks_remaining,
    )

    return WeeklyVolumeTarget(
        previous_duration_minutes=(
            previous_duration_minutes
        ),
        theoretical_duration_minutes=(
            theoretical_duration_minutes
        ),
        target_duration_minutes=(
            target_duration_minutes
        ),
        phase=phase,
        progression_limited=(
            progression_limited
        ),
        goal_demand_minutes=(
            goal_demand_minutes
        ),
        reachable_duration_ceiling_minutes=(
            reachable_duration_ceiling_minutes
        ),
        goal_demand_reachable=(
            goal_demand_reachable
        ),
    )


def _resolve_goal_reachability(
    *,
    previous_duration_minutes: float,
    maximum_progression_rate: float,
    goal_demand_minutes: float | None,
    weeks_remaining: int | None,
) -> tuple[
    float | None,
    bool | None,
]:
    """Estime le plafond mathématique atteignable dans le délai."""

    if goal_demand_minutes is None:
        return (
            None,
            None,
        )

    assert weeks_remaining is not None

    reachable_duration_ceiling_minutes = (
        previous_duration_minutes
        * (
            1.0
            + maximum_progression_rate
        )
        ** weeks_remaining
    )

    return (
        reachable_duration_ceiling_minutes,
        (
            goal_demand_minutes
            <= reachable_duration_ceiling_minutes
        ),
    )
