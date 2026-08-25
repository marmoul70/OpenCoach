import pytest

from opencoach.planning.sessions.prescription.distance_target import (
    calculate_distance_repetition_target,
)


def test_distance_target_uses_vma_percentage_range() -> None:
    target = calculate_distance_repetition_target(
        distance_meters=200,
        vma_kmh=15.0,
        vma_percent_min=100.0,
        vma_percent_max=115.0,
    )

    assert target.fast_seconds == pytest.approx(
        41.74,
        abs=0.01,
    )

    assert target.slow_seconds == pytest.approx(
        48.0,
        abs=0.01,
    )


def test_distance_target_exposes_rounded_seconds() -> None:
    target = calculate_distance_repetition_target(
        distance_meters=200,
        vma_kmh=15.0,
        vma_percent_min=100.0,
        vma_percent_max=115.0,
    )

    assert target.rounded_fast_seconds == 42
    assert target.rounded_slow_seconds == 48


@pytest.mark.parametrize(
    (
        "distance_meters",
        "vma_kmh",
        "vma_percent_min",
        "vma_percent_max",
    ),
    (
        (0, 15.0, 100.0, 115.0),
        (200, 0.0, 100.0, 115.0),
        (200, 15.0, 0.0, 115.0),
        (200, 15.0, 115.0, 100.0),
    ),
)
def test_distance_target_rejects_invalid_values(
    distance_meters: int,
    vma_kmh: float,
    vma_percent_min: float,
    vma_percent_max: float,
) -> None:
    with pytest.raises(ValueError):
        calculate_distance_repetition_target(
            distance_meters=distance_meters,
            vma_kmh=vma_kmh,
            vma_percent_min=vma_percent_min,
            vma_percent_max=vma_percent_max,
        )
