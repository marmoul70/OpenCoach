from pathlib import Path

from opencoach.services.system_notification_state import (
    SystemNotificationState,
)


def test_first_failure_should_notify(
    tmp_path: Path,
) -> None:
    state = SystemNotificationState(
        tmp_path / "state.json"
    )

    assert state.should_notify(
        "intervals_sync"
    )


def test_failure_is_deduplicated(
    tmp_path: Path,
) -> None:
    state = SystemNotificationState(
        tmp_path / "state.json"
    )

    state.mark_failed(
        "intervals_sync"
    )

    assert not state.should_notify(
        "intervals_sync"
    )


def test_success_rearms_notification(
    tmp_path: Path,
) -> None:
    state = SystemNotificationState(
        tmp_path / "state.json"
    )

    state.mark_failed(
        "intervals_sync"
    )

    assert not state.should_notify(
        "intervals_sync"
    )

    state.mark_success(
        "intervals_sync"
    )

    assert state.should_notify(
        "intervals_sync"
    )


def test_events_are_independent(
    tmp_path: Path,
) -> None:
    state = SystemNotificationState(
        tmp_path / "state.json"
    )

    state.mark_failed(
        "intervals_sync"
    )

    assert not state.should_notify(
        "intervals_sync"
    )

    assert state.should_notify(
        "backup"
    )
