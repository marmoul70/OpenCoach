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

def test_partner_sync_failure_does_not_block_incremental_sync(
    monkeypatch,
) -> None:
    calls = {
        "partner": 0,
        "incremental": 0,
    }

    class FakeClient:
        def trigger_partner_sync(self) -> None:
            calls["partner"] += 1
            raise RuntimeError(
                "partner sync unavailable"
            )

    class FakeResult:
        synced_wellness_days = 1

    class FakeService:
        def sync_incremental(
            self,
            profile_id,
        ):
            calls["incremental"] += 1
            return FakeResult()

    class FakeWellnessRepository:
        def __init__(
            self,
            session,
        ) -> None:
            self.session = session

        def get_by_date(
            self,
            profile_id,
            wellness_date,
            *,
            provider,
        ):
            return None

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False

    monkeypatch.setattr(
        "opencoach.commands.refresh_daily_health.SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        "opencoach.commands.refresh_daily_health."
        "list_intervals_sync_targets",
        lambda session: [
            SimpleNamespace(
                user_id=456,
                athlete_profile_id=123,
            )
        ],
    )

    monkeypatch.setattr(
        "opencoach.commands.refresh_daily_health."
        "SqlWellnessRepository",
        FakeWellnessRepository,
    )

    monkeypatch.setattr(
        "opencoach.commands.refresh_daily_health."
        "_build_intervals_client",
        lambda session, profile_id: FakeClient(),
    )

    monkeypatch.setattr(
        "opencoach.commands.refresh_daily_health."
        "build_service",
        lambda session, profile_id: FakeService(),
    )

    monkeypatch.setattr(
        "opencoach.commands.refresh_daily_health.time.sleep",
        lambda seconds: None,
    )

    monkeypatch.setattr(
        "opencoach.commands.refresh_daily_health.datetime",
        type(
            "FakeDateTime",
            (),
            {
                "now": staticmethod(
                    lambda: datetime(
                        2026,
                        9,
                        2,
                        8,
                        15,
                    )
                )
            },
        ),
    )

    from opencoach.commands.refresh_daily_health import main

    result = main([])

    assert result == 0
    assert calls["partner"] == 1
    assert calls["incremental"] == 1
