"""Réconciliation entre charge planifiée et charge réalisée.

Ce module compare la charge réellement effectuée par l'athlète
avec la charge prévue par la trajectoire.

Il décrit l'écart observé mais ne décide pas encore comment
la trajectoire suivante doit être modifiée.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LoadReconciliationStatus(StrEnum):
    """Classification de l'écart entre prévu et réalisé."""

    ON_TARGET = "on_target"

    UNDER_TARGET = "under_target"
    STRONGLY_UNDER_TARGET = "strongly_under_target"

    OVER_TARGET = "over_target"
    STRONGLY_OVER_TARGET = "strongly_over_target"


@dataclass(frozen=True, slots=True)
class WeeklyLoadReconciliation:
    """Résultat de comparaison d'une semaine planifiée et réalisée."""

    planned_load: float
    actual_load: float

    absolute_delta: float
    relative_delta: float

    status: LoadReconciliationStatus

    def __post_init__(self) -> None:
        if self.planned_load < 0:
            raise ValueError(
                "La charge planifiée ne peut pas être négative."
            )

        if self.actual_load < 0:
            raise ValueError(
                "La charge réalisée ne peut pas être négative."
            )


ON_TARGET_TOLERANCE = 0.10
STRONG_DEVIATION_THRESHOLD = 0.25


def reconcile_weekly_load(
    *,
    planned_load: float,
    actual_load: float,
) -> WeeklyLoadReconciliation:
    """Compare la charge prévue à la charge réellement effectuée.

    Les seuils sont relatifs à la charge planifiée :

    - entre -10 % et +10 % : conforme ;
    - entre -25 % et -10 % : sous la cible ;
    - sous -25 % : fortement sous la cible ;
    - entre +10 % et +25 % : au-dessus de la cible ;
    - au-dessus de +25 % : fortement au-dessus de la cible.
    """

    if planned_load < 0:
        raise ValueError(
            "La charge planifiée ne peut pas être négative."
        )

    if actual_load < 0:
        raise ValueError(
            "La charge réalisée ne peut pas être négative."
        )

    absolute_delta = (
        actual_load
        - planned_load
    )

    relative_delta = _calculate_relative_delta(
        planned_load=planned_load,
        actual_load=actual_load,
    )

    status = _classify_relative_delta(
        planned_load=planned_load,
        actual_load=actual_load,
        relative_delta=relative_delta,
    )

    return WeeklyLoadReconciliation(
        planned_load=planned_load,
        actual_load=actual_load,
        absolute_delta=absolute_delta,
        relative_delta=relative_delta,
        status=status,
    )


def _calculate_relative_delta(
    *,
    planned_load: float,
    actual_load: float,
) -> float:
    """Calcule l'écart relatif par rapport à la charge prévue."""

    if planned_load == 0:
        return (
            0.0
            if actual_load == 0
            else 1.0
        )

    return (
        actual_load
        - planned_load
    ) / planned_load


def _classify_relative_delta(
    *,
    planned_load: float,
    actual_load: float,
    relative_delta: float,
) -> LoadReconciliationStatus:
    """Classe l'écart observé."""

    if planned_load == 0:
        if actual_load == 0:
            return LoadReconciliationStatus.ON_TARGET

        return (
            LoadReconciliationStatus.STRONGLY_OVER_TARGET
        )

    if relative_delta < -STRONG_DEVIATION_THRESHOLD:
        return (
            LoadReconciliationStatus.STRONGLY_UNDER_TARGET
        )

    if relative_delta < -ON_TARGET_TOLERANCE:
        return LoadReconciliationStatus.UNDER_TARGET

    if relative_delta <= ON_TARGET_TOLERANCE:
        return LoadReconciliationStatus.ON_TARGET

    if relative_delta <= STRONG_DEVIATION_THRESHOLD:
        return LoadReconciliationStatus.OVER_TARGET

    return LoadReconciliationStatus.STRONGLY_OVER_TARGET
