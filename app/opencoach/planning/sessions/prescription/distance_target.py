"""Calcul des temps de passage pour les répétitions métriques."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DistanceRepetitionTarget:
    """Plage temporelle associée à une répétition métrique."""

    distance_meters: int

    vma_kmh: float

    vma_percent_min: float
    vma_percent_max: float

    fast_seconds: float
    slow_seconds: float

    @property
    def rounded_fast_seconds(
        self,
    ) -> int:
        return round(
            self.fast_seconds
        )

    @property
    def rounded_slow_seconds(
        self,
    ) -> int:
        return round(
            self.slow_seconds
        )


def calculate_distance_repetition_target(
    *,
    distance_meters: int,
    vma_kmh: float,
    vma_percent_min: float,
    vma_percent_max: float,
) -> DistanceRepetitionTarget:
    """Calcule une plage de temps à partir de la VMA.

    La borne rapide utilise le pourcentage de VMA maximal.
    La borne lente utilise le pourcentage minimal.
    """

    if distance_meters <= 0:
        raise ValueError(
            "La distance doit être strictement positive."
        )

    if vma_kmh <= 0:
        raise ValueError(
            "La VMA doit être strictement positive."
        )

    if vma_percent_min <= 0:
        raise ValueError(
            "Le pourcentage minimal de VMA doit être positif."
        )

    if (
        vma_percent_max
        < vma_percent_min
    ):
        raise ValueError(
            "Le pourcentage maximal de VMA "
            "ne peut pas être inférieur au minimum."
        )

    fast_speed_mps = (
        vma_kmh
        * (
            vma_percent_max
            / 100
        )
        / 3.6
    )

    slow_speed_mps = (
        vma_kmh
        * (
            vma_percent_min
            / 100
        )
        / 3.6
    )

    fast_seconds = (
        distance_meters
        / fast_speed_mps
    )

    slow_seconds = (
        distance_meters
        / slow_speed_mps
    )

    return DistanceRepetitionTarget(
        distance_meters=distance_meters,
        vma_kmh=vma_kmh,
        vma_percent_min=vma_percent_min,
        vma_percent_max=vma_percent_max,
        fast_seconds=fast_seconds,
        slow_seconds=slow_seconds,
    )
