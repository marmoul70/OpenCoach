"""Profil des demandes d'une course cible.

Ce module transforme les caractéristiques objectives d'une course
en besoins relatifs pour la trajectoire d'entraînement.

Il ne génère aucune séance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RaceDistanceCategory(StrEnum):
    SHORT = "short"
    MIDDLE = "middle"
    LONG = "long"
    ULTRA = "ultra"


class ElevationDemand(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RaceSpecificityDemand(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True, slots=True)
class RaceDemandProfile:
    """Demandes relatives produites à partir de la course cible."""

    distance_km: float

    elevation_gain_m: float

    distance_category: RaceDistanceCategory
    elevation_demand: ElevationDemand

    endurance_demand: RaceSpecificityDemand
    long_endurance_demand: RaceSpecificityDemand
    uphill_demand: RaceSpecificityDemand
    downhill_demand: RaceSpecificityDemand
    threshold_demand: RaceSpecificityDemand
    race_specific_demand: RaceSpecificityDemand

    @property
    def elevation_ratio_m_per_km(self) -> float:
        if self.distance_km == 0:
            return 0.0

        return (
            self.elevation_gain_m
            / self.distance_km
        )


def classify_distance(
    distance_km: float,
) -> RaceDistanceCategory:
    if distance_km <= 0:
        raise ValueError(
            "La distance de course doit être strictement positive."
        )

    if distance_km <= 15:
        return RaceDistanceCategory.SHORT

    if distance_km <= 35:
        return RaceDistanceCategory.MIDDLE

    if distance_km <= 60:
        return RaceDistanceCategory.LONG

    return RaceDistanceCategory.ULTRA


def classify_elevation(
    *,
    distance_km: float,
    elevation_gain_m: float,
) -> ElevationDemand:
    if distance_km <= 0:
        raise ValueError(
            "La distance de course doit être strictement positive."
        )

    if elevation_gain_m < 0:
        raise ValueError(
            "Le dénivelé positif ne peut pas être négatif."
        )

    ratio = (
        elevation_gain_m
        / distance_km
    )

    if ratio < 10:
        return ElevationDemand.LOW

    if ratio < 30:
        return ElevationDemand.MODERATE

    if ratio < 50:
        return ElevationDemand.HIGH

    return ElevationDemand.VERY_HIGH


def build_race_demand_profile(
    *,
    distance_km: float,
    elevation_gain_m: float,
) -> RaceDemandProfile:
    """Construit le profil de demande d'une course."""

    distance_category = classify_distance(
        distance_km
    )

    elevation_demand = classify_elevation(
        distance_km=distance_km,
        elevation_gain_m=elevation_gain_m,
    )

    endurance_demand = _endurance_demand(
        distance_category
    )

    long_endurance_demand = _long_endurance_demand(
        distance_category
    )

    uphill_demand = _elevation_specific_demand(
        elevation_demand
    )

    downhill_demand = _elevation_specific_demand(
        elevation_demand
    )

    threshold_demand = _threshold_demand(
        distance_category
    )

    race_specific_demand = _race_specific_demand(
        distance_category=distance_category,
        elevation_demand=elevation_demand,
    )

    return RaceDemandProfile(
        distance_km=distance_km,
        elevation_gain_m=elevation_gain_m,
        distance_category=distance_category,
        elevation_demand=elevation_demand,
        endurance_demand=endurance_demand,
        long_endurance_demand=long_endurance_demand,
        uphill_demand=uphill_demand,
        downhill_demand=downhill_demand,
        threshold_demand=threshold_demand,
        race_specific_demand=race_specific_demand,
    )


def _endurance_demand(
    category: RaceDistanceCategory,
) -> RaceSpecificityDemand:
    if category is RaceDistanceCategory.SHORT:
        return RaceSpecificityDemand.MODERATE

    if category is RaceDistanceCategory.MIDDLE:
        return RaceSpecificityDemand.HIGH

    return RaceSpecificityDemand.VERY_HIGH


def _long_endurance_demand(
    category: RaceDistanceCategory,
) -> RaceSpecificityDemand:
    if category is RaceDistanceCategory.SHORT:
        return RaceSpecificityDemand.LOW

    if category is RaceDistanceCategory.MIDDLE:
        return RaceSpecificityDemand.MODERATE

    if category is RaceDistanceCategory.LONG:
        return RaceSpecificityDemand.HIGH

    return RaceSpecificityDemand.VERY_HIGH


def _elevation_specific_demand(
    demand: ElevationDemand,
) -> RaceSpecificityDemand:
    mapping = {
        ElevationDemand.LOW: RaceSpecificityDemand.LOW,
        ElevationDemand.MODERATE: RaceSpecificityDemand.MODERATE,
        ElevationDemand.HIGH: RaceSpecificityDemand.HIGH,
        ElevationDemand.VERY_HIGH: RaceSpecificityDemand.VERY_HIGH,
    }

    return mapping[demand]


def _threshold_demand(
    category: RaceDistanceCategory,
) -> RaceSpecificityDemand:
    if category is RaceDistanceCategory.SHORT:
        return RaceSpecificityDemand.VERY_HIGH

    if category is RaceDistanceCategory.MIDDLE:
        return RaceSpecificityDemand.HIGH

    if category is RaceDistanceCategory.LONG:
        return RaceSpecificityDemand.MODERATE

    return RaceSpecificityDemand.LOW


def _race_specific_demand(
    *,
    distance_category: RaceDistanceCategory,
    elevation_demand: ElevationDemand,
) -> RaceSpecificityDemand:
    if (
        distance_category
        in {
            RaceDistanceCategory.LONG,
            RaceDistanceCategory.ULTRA,
        }
        or elevation_demand
        in {
            ElevationDemand.HIGH,
            ElevationDemand.VERY_HIGH,
        }
    ):
        return RaceSpecificityDemand.VERY_HIGH

    if (
        distance_category is RaceDistanceCategory.MIDDLE
        or elevation_demand is ElevationDemand.MODERATE
    ):
        return RaceSpecificityDemand.HIGH

    return RaceSpecificityDemand.MODERATE
