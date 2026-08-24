"""Estimation déterministe de la demande de volume d'une course cible.

Cette brique transforme un profil objectif de course en une demande de
volume hebdomadaire de pic spécifique.

Elle ne prescrit pas directement ce volume à l'athlète.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.knowledge.race_demand_profile import (
    RaceDemandProfile,
)


@dataclass(frozen=True, slots=True)
class VolumeDemandPolicy:
    """Politique de calibration de la demande de volume."""

    base_minutes: float = 210.0
    minutes_per_effort_km: float = 2.0

    minimum_minutes: float = 180.0
    maximum_minutes: float = 600.0

    def __post_init__(self) -> None:
        values = (
            self.base_minutes,
            self.minutes_per_effort_km,
            self.minimum_minutes,
            self.maximum_minutes,
        )

        if any(
            value < 0
            for value in values
        ):
            raise ValueError(
                "Les paramètres de demande de volume "
                "ne peuvent pas être négatifs."
            )

        if (
            self.minimum_minutes
            > self.maximum_minutes
        ):
            raise ValueError(
                "La borne minimale de volume "
                "ne peut pas dépasser la borne maximale."
            )


@dataclass(frozen=True, slots=True)
class RaceVolumeDemand:
    """Demande de volume dérivée d'une course cible."""

    effort_distance_km: float

    raw_specific_peak_duration_minutes: float
    specific_peak_duration_minutes: float

    limited_by_minimum: bool
    limited_by_maximum: bool

    def __post_init__(self) -> None:
        values = (
            self.effort_distance_km,
            self.raw_specific_peak_duration_minutes,
            self.specific_peak_duration_minutes,
        )

        if any(
            value < 0
            for value in values
        ):
            raise ValueError(
                "Les valeurs de demande de volume "
                "ne peuvent pas être négatives."
            )


DEFAULT_VOLUME_DEMAND_POLICY = (
    VolumeDemandPolicy()
)


def build_race_volume_demand(
    *,
    race_profile: RaceDemandProfile,
    policy: VolumeDemandPolicy = (
        DEFAULT_VOLUME_DEMAND_POLICY
    ),
) -> RaceVolumeDemand:
    """Construit la demande de volume de pic spécifique."""

    effort_distance_km = (
        race_profile.distance_km
        + race_profile.elevation_gain_m
        / 100.0
    )

    raw_specific_peak_duration_minutes = (
        policy.base_minutes
        + (
            effort_distance_km
            * policy.minutes_per_effort_km
        )
    )

    specific_peak_duration_minutes = min(
        policy.maximum_minutes,
        max(
            policy.minimum_minutes,
            raw_specific_peak_duration_minutes,
        ),
    )

    limited_by_minimum = (
        specific_peak_duration_minutes
        > raw_specific_peak_duration_minutes
    )

    limited_by_maximum = (
        specific_peak_duration_minutes
        < raw_specific_peak_duration_minutes
    )

    return RaceVolumeDemand(
        effort_distance_km=(
            effort_distance_km
        ),
        raw_specific_peak_duration_minutes=(
            raw_specific_peak_duration_minutes
        ),
        specific_peak_duration_minutes=(
            specific_peak_duration_minutes
        ),
        limited_by_minimum=(
            limited_by_minimum
        ),
        limited_by_maximum=(
            limited_by_maximum
        ),
    )
