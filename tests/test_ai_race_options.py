from types import SimpleNamespace
from uuid import UUID

from opencoach.api.ai import _extract_race_options


def test_extract_race_options_exposes_only_valid_calendar_entries():
    race_id = "123e4567-e89b-42d3-a456-426614174000"
    results = [
        SimpleNamespace(
            tool="race_calendar",
            status="ok",
            data={
                "races": [
                    {
                        "race_id": race_id,
                        "date": "2026-12-01",
                        "name": "Ultra des Vosges",
                        "location": "Vosges",
                        "race_type": "trail",
                        "priority": "primary",
                        "status": "planned",
                        "distance_km": 65,
                        "elevation_gain_m": 3100,
                        "target_time_minutes": 600,
                    },
                    {
                        "race_id": "not-a-uuid",
                        "date": "2026-12-02",
                        "name": "Entrée invalide",
                    },
                ]
            },
        ),
        SimpleNamespace(
            tool="training_history",
            status="ok",
            data={"races": [{"race_id": race_id}]},
        ),
    ]

    options = _extract_race_options(results)

    assert len(options) == 1
    assert options[0].race_id == UUID(race_id)
    assert options[0].name == "Ultra des Vosges"
    assert options[0].distance_km == 65
    assert options[0].elevation_gain_m == 3100


def test_extract_race_options_returns_empty_for_empty_or_failed_calendar():
    results = [
        SimpleNamespace(tool="race_calendar", status="failed", data=None),
        SimpleNamespace(tool="race_calendar", status="ok", data={"races": []}),
    ]

    assert _extract_race_options(results) == []
