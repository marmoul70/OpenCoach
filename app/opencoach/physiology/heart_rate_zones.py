from dataclasses import dataclass

from opencoach.models.profile import (
    AthletePhysiology,
)


@dataclass(frozen=True, slots=True)
class HeartRatePrescription:
    zone: str
    min_bpm: int | None
    max_bpm: int


def get_heart_rate_zone(
    physiology: AthletePhysiology,
    zone_name: str,
) -> HeartRatePrescription | None:
    names = (
        "z1",
        "z2",
        "z3",
        "z4",
        "z5",
    )

    normalized = zone_name.lower()

    if normalized not in names:
        return None

    index = names.index(
            normalized,
        )

    zone = getattr(
        physiology.heart_rate_zones,
        normalized,
    )

    if zone is None:
        return None

    minimum: int | None = None

    if index > 0:
        previous = getattr(
            physiology.heart_rate_zones,
            names[index - 1],
        )

        if previous is not None:
            minimum = (
                previous.max_bpm
                + 1
            )

    return HeartRatePrescription(
        zone=normalized.upper(),
        min_bpm=minimum,
        max_bpm=zone.max_bpm,
    )


def resolve_heart_rate_zone(
    physiology: AthletePhysiology,
    bpm: int,
) -> str | None:
    for name in (
        "z1",
        "z2",
        "z3",
        "z4",
        "z5",
    ):
        zone = getattr(
            physiology.heart_rate_zones,
            name,
        )

        if (
            zone is not None
            and bpm <= zone.max_bpm
        ):
            return name.upper()

    return None
