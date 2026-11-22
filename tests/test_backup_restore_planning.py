from types import SimpleNamespace

from opencoach.api.backups import _planning_profile_skip_reason


def test_restore_planning_requires_weekly_session_target() -> None:
    training = SimpleNamespace(
        weekly_sessions=None,
        available_days=[0, 2, 4],
    )

    assert _planning_profile_skip_reason(training) is not None


def test_restore_planning_requires_available_training_days() -> None:
    training = SimpleNamespace(
        weekly_sessions=4,
        available_days=[],
    )

    assert _planning_profile_skip_reason(training) is not None


def test_restore_planning_rejects_invalid_weekday() -> None:
    training = SimpleNamespace(
        weekly_sessions=4,
        available_days=[0, 2, 7],
    )

    assert _planning_profile_skip_reason(training) is not None


def test_restore_planning_accepts_complete_training_schedule() -> None:
    training = SimpleNamespace(
        weekly_sessions=4,
        available_days=[0, 2, 4, 6],
    )

    assert _planning_profile_skip_reason(training) is None
