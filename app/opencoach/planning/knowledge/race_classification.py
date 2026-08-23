from dataclasses import dataclass
from typing import Literal

from opencoach.models import Race

from opencoach.planning.knowledge.training import (
    KnowledgeApplicability,
)


RaceSportFamily = Literal[
    "road",
    "trail",
    "other",
]

RaceDistanceFamily = Literal[
    "short",
    "middle",
    "long",
    "ultra",
    "unknown",
]

RaceElevationProfile = Literal[
    "flat",
    "rolling",
    "mountain",
    "unknown",
]


@dataclass(frozen=True)
class RaceClassificationThresholds:
    """Seuils configurables utilisés pour classifier une course."""

    road_short_max_km: float
    road_middle_max_km: float
    road_long_max_km: float

    trail_short_max_km: float
    trail_middle_max_km: float
    trail_long_max_km: float

    rolling_elevation_ratio: float
    mountain_elevation_ratio: float

    def __post_init__(self) -> None:
        if not (
            0
            < self.road_short_max_km
            < self.road_middle_max_km
            < self.road_long_max_km
        ):
            raise ValueError(
                "Les seuils route doivent être strictement croissants."
            )

        if not (
            0
            < self.trail_short_max_km
            < self.trail_middle_max_km
            < self.trail_long_max_km
        ):
            raise ValueError(
                "Les seuils trail doivent être strictement croissants."
            )

        if not (
            0
            <= self.rolling_elevation_ratio
            < self.mountain_elevation_ratio
        ):
            raise ValueError(
                "Les seuils de dénivelé doivent être cohérents."
            )


@dataclass(frozen=True)
class RaceKnowledgeClassification:
    """Classification explicable d'une course pour la knowledge base."""

    sport_family: RaceSportFamily

    distance_family: RaceDistanceFamily

    elevation_profile: RaceElevationProfile

    applicabilities: tuple[
        KnowledgeApplicability,
        ...
    ]

    reasons: tuple[
        str,
        ...
    ]


def classify_race_for_knowledge(
    *,
    race: Race,
    thresholds: RaceClassificationThresholds,
) -> RaceKnowledgeClassification:
    """Classe une course sans incorporer de logique de coaching."""

    sport_family = _classify_sport_family(
        race
    )

    distance_family = _classify_distance_family(
        race=race,
        sport_family=sport_family,
        thresholds=thresholds,
    )

    elevation_profile = _classify_elevation_profile(
        race=race,
        thresholds=thresholds,
    )

    applicabilities = _build_applicabilities(
        sport_family=sport_family,
        distance_family=distance_family,
    )

    reasons = (
        f"Sport classé comme {sport_family}.",
        (
            "Distance classée comme "
            f"{distance_family}."
        ),
        (
            "Profil de dénivelé classé comme "
            f"{elevation_profile}."
        ),
    )

    return RaceKnowledgeClassification(
        sport_family=sport_family,
        distance_family=distance_family,
        elevation_profile=elevation_profile,
        applicabilities=applicabilities,
        reasons=reasons,
    )


def _classify_sport_family(
    race: Race,
) -> RaceSportFamily:
    normalized = race.race_type.strip().lower()

    if normalized == "trail":
        return "trail"

    if normalized in {
        "road",
        "run",
        "running",
    }:
        return "road"

    return "other"


def _classify_distance_family(
    *,
    race: Race,
    sport_family: RaceSportFamily,
    thresholds: RaceClassificationThresholds,
) -> RaceDistanceFamily:
    distance = race.distance_km

    if sport_family == "other":
        return "unknown"

    if sport_family == "trail":
        if distance <= thresholds.trail_short_max_km:
            return "short"

        if distance <= thresholds.trail_middle_max_km:
            return "middle"

        if distance <= thresholds.trail_long_max_km:
            return "long"

        return "ultra"

    if distance <= thresholds.road_short_max_km:
        return "short"

    if distance <= thresholds.road_middle_max_km:
        return "middle"

    if distance <= thresholds.road_long_max_km:
        return "long"

    return "ultra"


def _classify_elevation_profile(
    *,
    race: Race,
    thresholds: RaceClassificationThresholds,
) -> RaceElevationProfile:
    elevation = race.elevation_gain_m

    if elevation is None:
        return "unknown"

    if race.distance_km <= 0:
        return "unknown"

    ratio = (
        elevation
        / race.distance_km
    )

    if ratio < thresholds.rolling_elevation_ratio:
        return "flat"

    if ratio < thresholds.mountain_elevation_ratio:
        return "rolling"

    return "mountain"


def _build_applicabilities(
    *,
    sport_family: RaceSportFamily,
    distance_family: RaceDistanceFamily,
) -> tuple[KnowledgeApplicability, ...]:
    values: list[
        KnowledgeApplicability
    ] = [
        "general_endurance",
    ]

    if sport_family == "road":
        values.append(
            "road_running"
        )

        if distance_family == "short":
            values.append(
                "10k"
            )

        elif distance_family == "middle":
            values.append(
                "half_marathon"
            )

        elif distance_family == "long":
            values.append(
                "marathon"
            )

    elif sport_family == "trail":
        values.append(
            "trail_running"
        )

        if distance_family == "short":
            values.append(
                "short_trail"
            )

        elif distance_family in {
            "middle",
            "long",
        }:
            values.append(
                "long_trail"
            )

        elif distance_family == "ultra":
            values.append(
                "ultra_trail"
            )

    return tuple(values)