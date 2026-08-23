"""Reconnexion progressive vers une référence structurelle de charge.

Après un réancrage, la référence structurelle peut rester sensiblement
supérieure à la charge récemment réalisée par l'athlète.

Ce module construit une rampe déterministe entre :
- la capacité récente observée ;
- la référence structurelle réancrée.

Les taux définis ici sont des paramètres de planification OpenCoach.
Ils constituent des garde-fous logiciels configurables et non des
seuils médicaux universels.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReconnectionStatus(StrEnum):
    """État de la reconnexion vers la référence structurelle."""

    NOT_REQUIRED = "not_required"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class TrajectoryReconnectionPolicy:
    """Politique de reconnexion progressive."""

    maximum_weekly_increase: float = 0.10
    completion_tolerance: float = 0.05

    def __post_init__(self) -> None:
        if self.maximum_weekly_increase < 0:
            raise ValueError(
                "La progression maximale ne peut pas être négative."
            )

        if not 0.0 <= self.completion_tolerance <= 1.0:
            raise ValueError(
                "La tolérance de reconnexion doit être comprise "
                "entre 0 et 1."
            )


@dataclass(frozen=True, slots=True)
class TrajectoryReconnection:
    """Décision de reconnexion pour une semaine."""

    status: ReconnectionStatus

    observed_load: float
    structural_reference_load: float

    target_load: float

    gap_before: float
    gap_after: float

    increase_rate: float

    structural_reference_reached: bool

    reasons: tuple[str, ...]


DEFAULT_RECONNECTION_POLICY = (
    TrajectoryReconnectionPolicy()
)


def calculate_trajectory_reconnection(
    *,
    observed_load: float,
    structural_reference_load: float,
    policy: TrajectoryReconnectionPolicy = (
        DEFAULT_RECONNECTION_POLICY
    ),
) -> TrajectoryReconnection:
    """Calcule la prochaine étape vers la référence structurelle."""

    if observed_load < 0:
        raise ValueError(
            "La charge observée ne peut pas être négative."
        )

    if structural_reference_load < 0:
        raise ValueError(
            "La référence structurelle ne peut pas être négative."
        )

    gap_before = max(
        0.0,
        structural_reference_load - observed_load,
    )

    if structural_reference_load == 0:
        return TrajectoryReconnection(
            status=ReconnectionStatus.NOT_REQUIRED,
            observed_load=observed_load,
            structural_reference_load=(
                structural_reference_load
            ),
            target_load=0.0,
            gap_before=0.0,
            gap_after=0.0,
            increase_rate=0.0,
            structural_reference_reached=True,
            reasons=(
                "La référence structurelle est nulle.",
            ),
        )

    tolerance_load = (
        structural_reference_load
        * policy.completion_tolerance
    )

    if observed_load >= structural_reference_load:
        return TrajectoryReconnection(
            status=ReconnectionStatus.NOT_REQUIRED,
            observed_load=observed_load,
            structural_reference_load=(
                structural_reference_load
            ),
            target_load=structural_reference_load,
            gap_before=0.0,
            gap_after=0.0,
            increase_rate=0.0,
            structural_reference_reached=True,
            reasons=(
                "La charge observée atteint déjà "
                "la référence structurelle.",
            ),
        )

    if gap_before <= tolerance_load:
        increase_rate = (
            (
                structural_reference_load
                - observed_load
            )
            / observed_load
            if observed_load > 0
            else 0.0
        )

        return TrajectoryReconnection(
            status=ReconnectionStatus.COMPLETED,
            observed_load=observed_load,
            structural_reference_load=(
                structural_reference_load
            ),
            target_load=structural_reference_load,
            gap_before=gap_before,
            gap_after=0.0,
            increase_rate=increase_rate,
            structural_reference_reached=True,
            reasons=(
                "L'écart résiduel appartient à la tolérance "
                "de reconnexion.",
            ),
        )

    if observed_load == 0:
        return TrajectoryReconnection(
            status=ReconnectionStatus.ACTIVE,
            observed_load=observed_load,
            structural_reference_load=(
                structural_reference_load
            ),
            target_load=0.0,
            gap_before=gap_before,
            gap_after=gap_before,
            increase_rate=0.0,
            structural_reference_reached=False,
            reasons=(
                "Aucune charge récente exploitable ne permet "
                "une progression relative automatique.",
            ),
        )

    maximum_target = (
        observed_load
        * (
            1.0
            + policy.maximum_weekly_increase
        )
    )

    target_load = min(
        structural_reference_load,
        maximum_target,
    )

    gap_after = max(
        0.0,
        structural_reference_load - target_load,
    )

    increase_rate = (
        target_load - observed_load
    ) / observed_load

    reached = (
        target_load
        >= structural_reference_load
    )

    return TrajectoryReconnection(
        status=(
            ReconnectionStatus.COMPLETED
            if reached
            else ReconnectionStatus.ACTIVE
        ),
        observed_load=observed_load,
        structural_reference_load=(
            structural_reference_load
        ),
        target_load=target_load,
        gap_before=gap_before,
        gap_after=gap_after,
        increase_rate=increase_rate,
        structural_reference_reached=reached,
        reasons=(
            (
                "La référence structurelle est atteinte "
                "progressivement."
            )
            if reached
            else (
                "La cible est temporairement bornée par "
                "la capacité récemment observée."
            ),
        ),
    )
