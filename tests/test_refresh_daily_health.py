from datetime import datetime
from types import SimpleNamespace

from opencoach.commands.refresh_daily_health import (
    _health_data_available,
    _is_final_check,
    _within_refresh_window,
)


def wellness(
    **values,
):
    defaults = {
        "hrv": None,
        "resting_hr": None,
        "sleep_seconds": None,
        "sleep_score": None,
        "avg_sleeping_hr": None,
        "spo2": None,
    }

    defaults.update(
        values
    )

    return SimpleNamespace(
        **defaults
    )


def test_missing_wellness_is_not_available():
    assert not _health_data_available(
        None
    )


def test_ctl_only_is_not_health_data():
    item = wellness()

    item.fitness_ctl = 50

    assert not _health_data_available(
        item
    )


def test_hrv_marks_health_as_available():
    assert _health_data_available(
        wellness(
            hrv=52,
        )
    )


def test_sleep_marks_health_as_available():
    assert _health_data_available(
        wellness(
            sleep_seconds=28000,
        )
    )


def test_refresh_window_starts_at_8():
    assert _within_refresh_window(
        datetime(
            2026,
            9,
            2,
            8,
            0,
        )
    )


def test_refresh_window_excludes_7():
    assert not _within_refresh_window(
        datetime(
            2026,
            9,
            2,
            7,
            59,
        )
    )


def test_final_check_from_10():
    assert _is_final_check(
        datetime(
            2026,
            9,
            2,
            10,
            0,
        )
    )
