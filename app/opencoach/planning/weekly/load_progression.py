"""Progression déterministe de la charge hebdomadaire.

Ce module calcule une cible de charge relative pour la semaine suivante.
Il ne choisit ni sport, ni séance, ni contenu d'entraînement.

La charge est volontairement exprimée dans une unité abstraite afin de
ne pas coupler la trajectoire à une métrique particulière.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


@dataclass(frozen=True, slots=True)
class LoadProgressionPolicy:
    """Politique de progression associée à une phase."""

    phase: TrainingPhase

    progression_rate: float
    tolerance_below: float
    tolerance_above: float

    def __post_init__(self) -> None:
        if self.progression_rate < -1.0:
            raise ValueError(
                "Le taux de progression ne peut pas être inférieur à -100 %."
            )

        if self.tolerance_below < 0:
            raise ValueError(
                "La tolérance basse ne peut pas être négative."
            )

        if self.tolerance_above < 0:
            raise ValueError(
                "La tolérance haute ne peut pas être négative."
            )


@dataclass(frozen=True, slots=True)
class WeeklyLoadTarget:
    """Cible de charge calculée par le moteur."""

    previous_load: float

    theoretical_load: float
    target_load: float

    load_min: float
    load_max: float

    phase: TrainingPhase

    adjustment: LoadAdjustment

    def __post_init__(self) -> None:
        values = (
            self.previous_load,
            self.theoretical_load,
            self.target_load,
            self.load_min,
            self.load_max,
        )

        if any(value < 0 for value in values):
            raise ValueError(
                "Les valeurs de charge ne peuvent pas être négatives."
            )

        if self.load_min > self.load_max:
            raise ValueError(
                "La charge minimale ne peut pas dépasser "
                "la charge maximale."
            )

        if not (
            self.load_min
            <= self.target_load
            <= self.load_max
        ):
            raise ValueError(
                "La charge cible doit appartenir à la plage autorisée."
            )


DEFAULT_LOAD_POLICIES = {
    TrainingPhase.FOUNDATION: LoadProgressionPolicy(
        phase=TrainingPhase.FOUNDATION,
        progression_rate=0.03,
        tolerance_below=0.05,
        tolerance_above=0.05,
    ),
    TrainingPhase.BASE: LoadProgressionPolicy(
        phase=TrainingPhase.BASE,
        progression_rate=0.04,
        tolerance_below=0.05,
        tolerance_above=0.05,
    ),
    TrainingPhase.BUILD: LoadProgressionPolicy(
        phase=TrainingPhase.BUILD,
        progression_rate=0.06,
        tolerance_below=0.05,
        tolerance_above=0.05,
    ),
    TrainingPhase.SPECIFIC: LoadProgressionPolicy(
        phase=TrainingPhase.SPECIFIC,
        progression_rate=0.02,
        tolerance_below=0.05,
        tolerance_above=0.05,
    ),
    TrainingPhase.TAPER: LoadProgressionPolicy(
        phase=TrainingPhase.TAPER,
        progression_rate=-0.30,
        tolerance_below=0.10,
        tolerance_above=0.05,
    ),
    TrainingPhase.RECOVERY: LoadProgressionPolicy(
        phase=TrainingPhase.RECOVERY,
        progression_rate=-0.35,
        tolerance_below=0.10,
        tolerance_above=0.05,
    ),
    TrainingPhase.RETURN_TO_TRAINING: LoadProgressionPolicy(
        phase=TrainingPhase.RETURN_TO_TRAINING,
        progression_rate=-0.20,
        tolerance_below=0.10,
        tolerance_above=0.05,
    ),
}


ADJUSTMENT_FACTORS = {
    LoadAdjustment.MAINTAIN: 1.0,
    LoadAdjustment.REDUCE_SLIGHTLY: 0.90,
    LoadAdjustment.REDUCE: 0.75,
    LoadAdjustment.REDUCE_STRONGLY: 0.50,
    LoadAdjustment.SUSPEND: 0.0,
}


def calculate_weekly_load_target(
    *,
    previous_load: float,
    phase: TrainingPhase,
    adjustment: LoadAdjustment = LoadAdjustment.MAINTAIN,
    policies: dict[
        TrainingPhase,
        LoadProgressionPolicy,
    ] = DEFAULT_LOAD_POLICIES,
) -> WeeklyLoadTarget:
    """Calcule la cible de charge de la semaine suivante."""

    if previous_load < 0:
        raise ValueError(
            "La charge précédente ne peut pas être négative."
        )

    try:
        policy = policies[phase]
    except KeyError as exc:
        raise ValueError(
            f"Aucune politique de charge pour la phase {phase}."
        ) from exc

    theoretical_load = max(
        0.0,
        previous_load
        * (1.0 + policy.progression_rate),
    )

    factor = ADJUSTMENT_FACTORS[
        adjustment
    ]

    target_load = (
        theoretical_load
        * factor
    )

    load_min = max(
        0.0,
        target_load
        * (1.0 - policy.tolerance_below),
    )

    load_max = max(
        load_min,
        target_load
        * (1.0 + policy.tolerance_above),
    )

    return WeeklyLoadTarget(
        previous_load=previous_load,
        theoretical_load=theoretical_load,
        target_load=target_load,
        load_min=load_min,
        load_max=load_max,
        phase=phase,
        adjustment=adjustment,
    )
