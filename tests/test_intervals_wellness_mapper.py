from datetime import date, datetime, timezone

import pytest

from opencoach.integrations.intervals import (
    IntervalsDataError,
    map_intervals_wellness,
)


def create_wellness_data() -> dict:
    return {
        "id": "2026-08-18",
        "ctl": 16.624886,
        "atl": 6.00268,
        "rampRate": -2.8922691,
        "steps": 1627,
        "updated": "2026-08-17T16:15:43.799+00:00",
    }


def test_intervals_wellness_is_mapped() -> None:
    wellness = map_intervals_wellness(
        create_wellness_data()
    )

    assert wellness.provider == "intervals"
    assert wellness.date == date(2026, 8, 18)

    assert wellness.fitness_ctl == 16.624886
    assert wellness.fatigue_atl == 6.00268
    assert wellness.ramp_rate == -2.8922691
    assert wellness.steps == 1627

    assert wellness.provider_updated_at == datetime(
        2026,
        8,
        17,
        16,
        15,
        43,
        799000,
        tzinfo=timezone.utc,
    )


def test_intervals_wellness_accepts_missing_optional_values() -> None:
    data = {
        "id": "2026-08-18",
        "ctl": 16.0,
        "atl": 6.0,
        "rampRate": -2.0,
        "steps": None,
        "updated": None,
    }

    wellness = map_intervals_wellness(data)

    assert wellness.steps is None
    assert wellness.provider_updated_at is None


def test_intervals_wellness_requires_date() -> None:
    data = create_wellness_data()
    data["id"] = None

    with pytest.raises(
        IntervalsDataError,
        match="Champ Wellness obligatoire absent",
    ):
        map_intervals_wellness(data)


def test_intervals_wellness_rejects_invalid_date() -> None:
    data = create_wellness_data()
    data["id"] = "invalid"

    with pytest.raises(
        IntervalsDataError,
        match="Date Wellness invalide",
    ):
        map_intervals_wellness(data)
