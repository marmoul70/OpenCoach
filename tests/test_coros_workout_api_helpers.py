from datetime import date, datetime, timezone

from opencoach.api.training_sessions import _as_utc
from opencoach.api.coros import (
    _extract_coros_scheduled_id,
    _extract_other_coros_workouts,
    _extract_scheduled_workout_records_for_date,
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
    expected_utc = datetime(2026, 11, 6, 12, 30, tzinfo=timezone.utc)
    aware_offset = datetime.fromisoformat("2026-11-06T13:30:00+01:00")

    assert _as_utc(naive) == expected_utc
    assert _as_utc(aware_offset) == expected_utc
    assert _as_utc(None) is None


def test_extracts_editability_and_course_from_scheduled_workout_details() -> None:
    from opencoach.api.coros import _extract_coros_scheduled_details

    details = _extract_coros_scheduled_details(
        {
            "structuredContent": {
                "metadata": {"editable": True},
                "workoutDetails": {
                    "course": {
                        "courseName": "Footing",
                        "sportType": 1,
                        "sections": [{"sectionType": 2, "targetType": 2, "targetValue": 1800}],
                    },
                },
            }
        }
    )

    assert details is not None
    assert details["editable"] is True
    assert details["course"]["courseName"] == "Footing"


def test_extracts_non_editable_reason_from_scheduled_workout_details() -> None:
    from opencoach.api.coros import _extract_coros_scheduled_details

    details = _extract_coros_scheduled_details(
        {
            "structuredContent": {
                "editable": False,
                "reasons": ["Séance terminée", "Date passée"],
            }
        }
    )

    assert details is not None
    assert details["editable"] is False
    assert details["reason"] == "Séance terminée; Date passée"



def test_extracts_scheduled_workout_from_iso_date_keyed_schedule() -> None:
    result = {
        "structuredContent": {
            "2026-11-12": {
                "workouts": [
                    {
                        "idInPlan": "9223372036854775001",
                        "courseName": "Footing aérobie",
                    }
                ]
            }
        }
    }

    assert _extract_scheduled_workout_records_for_date(
        result,
        date(2026, 11, 12),
    ) == [("9223372036854775001", "Footing aérobie")]


def test_extracts_scheduled_workout_from_iso_date_field() -> None:
    result = {
        "structuredContent": {
            "schedule": {
                "days": [
                    {
                        "date": "2026-11-12",
                        "workouts": [
                            {
                                "idInPlan": "9223372036854775002",
                                "courseName": "Footing aérobie",
                            }
                        ],
                    }
                ]
            }
        }
    }

    assert _extract_scheduled_workout_records_for_date(
        result,
        date(2026, 11, 12),
    ) == [("9223372036854775002", "Footing aérobie")]



def test_extracts_scheduled_workouts_from_coros_plain_text_schedule() -> None:
    from opencoach.api.coros import _extract_scheduled_workouts_for_date

    result = {
        "content": [
            {
                "type": "text",
                "text": (
                    "Training Schedule\n"
                    "========================\n\n"
                    "2026-11-12\n"
                    "Footing 35 min\n"
                    "Plan ID: 480641426263295064\n"
                    "idInPlan: 26\n"
                    "Distance: 4.53 km\n\n"
                    "2026-11-12\n"
                    "Test COROS - Endurance fondamentale\n"
                    "Standalone workout (scheduled from the workout library)\n"
                    "idInPlan: 10\n"
                    "Distance: 5.43 km\n"
                ),
            }
        ]
    }

    assert _extract_scheduled_workout_records_for_date(
        result,
        date(2026, 11, 12),
    ) == [
        ("26", "Footing 35 min"),
        ("10", "Test COROS - Endurance fondamentale"),
    ]
    assert _extract_scheduled_workouts_for_date(
        result,
        date(2026, 11, 12),
    ) == ["Footing 35 min", "Test COROS - Endurance fondamentale"]


def test_recovery_records_include_only_explicitly_standalone_workouts() -> None:
    from opencoach.api.coros import (
        _extract_standalone_scheduled_workout_records_for_date,
    )

    result = {
        "content": [
            {
                "type": "text",
                "text": (
                    "Training Schedule\n"
                    "========================\n\n"
                    "2026-11-12\n"
                    "Footing 35 min\n"
                    "Plan ID: 480641426263295064\n"
                    "idInPlan: 26\n"
                    "Distance: 4.53 km\n\n"
                    "2026-11-12\n"
                    "Test COROS - Endurance fondamentale\n"
                    "Standalone workout (scheduled from the workout library)\n"
                    "idInPlan: 10\n"
                    "Distance: 5.43 km\n"
                ),
            }
        ]
    }

    assert _extract_standalone_scheduled_workout_records_for_date(
        result,
        date(2026, 11, 12),
    ) == [("10", "Test COROS - Endurance fondamentale")]
