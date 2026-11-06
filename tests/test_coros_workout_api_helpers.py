from datetime import datetime, timezone

from opencoach.api.training_sessions import _as_utc
from opencoach.api.coros import (
    _extract_coros_scheduled_id,
    _extract_other_coros_workouts,
)


def test_extracts_scheduled_id_from_structured_mcp_result() -> None:
    result = {
        "structuredContent": {
            "createdWorkout": {
                "idInPlan": "9223372036854775000",
            }
        }
    }

    assert _extract_coros_scheduled_id(result) == "9223372036854775000"


def test_extracts_scheduled_id_from_text_mcp_result() -> None:
    result = {
        "content": [
            {
                "type": "text",
                "text": 'Workout created successfully: {"idInPlan":"123456789"}',
            }
        ]
    }

    assert _extract_coros_scheduled_id(result) == "123456789"


def test_reports_other_workouts_but_not_the_new_workout() -> None:
    result = {
        "structuredContent": {
            "workouts": [
                {
                    "idInPlan": "new-id",
                    "courseName": "Footing aérobie",
                },
                {
                    "idInPlan": "existing-id",
                    "courseName": "Renforcement",
                },
                {
                    "idInPlan": "other-id",
                    "courseName": "Sortie longue",
                },
            ]
        }
    }

    assert _extract_other_coros_workouts(
        result,
        created_id="new-id",
        current_name="Footing aérobie",
    ) == ["Renforcement", "Sortie longue"]



def test_training_session_coros_timestamps_are_exposed_as_explicit_utc() -> None:
    naive = datetime(2026, 11, 6, 12, 30)
    aware = datetime(2026, 11, 6, 13, 30, tzinfo=timezone.utc)

    assert _as_utc(naive) == aware
    assert _as_utc(aware) is aware
    assert _as_utc(None) is None
