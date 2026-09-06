from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from opencoach.coaching.weekly_debrief_notification import (
    WeeklyDebriefNotificationService,
    WeeklyDebriefNotificationStatus,
)


WEEK_START = date(2026, 8, 31)


@dataclass
class FakeStored:
    planning_updated_at: datetime | None
    notification_sent_at: datetime | None


class FakeRepository:
    def __init__(self, stored):
        self.stored = stored
        self.mark_calls = []

    def get_for_week(
        self,
        athlete_profile_id,
        week_start,
    ):
        return self.stored

    def mark_notification_sent(
        self,
        athlete_profile_id,
        week_start,
        *,
        timestamp=None,
    ):
        self.mark_calls.append(
            (
                athlete_profile_id,
                week_start,
                timestamp,
            )
        )

        self.stored.notification_sent_at = timestamp
        return self.stored


class FakeSessionReader:
    def __init__(self, statuses=()):
        self.statuses = statuses
        self.calls = []

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return [
            SimpleNamespace(
                intervals_sync_status=status
            )
            for status in self.statuses
        ]


class FakePush:
    def __init__(
        self,
        *,
        sent=1,
        failed=0,
        removed=0,
        error=None,
    ):
        self.sent = sent
        self.failed = failed
        self.removed = removed
        self.error = error
        self.calls = []

    def send_weekly_debrief_notification(
        self,
        *,
        user_id,
        title,
        body,
        url="/training",
    ):
        self.calls.append(
            {
                "user_id": user_id,
                "title": title,
                "body": body,
                "url": url,
            }
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            sent=self.sent,
            failed=self.failed,
            removed=self.removed,
        )


def _ready_stored():
    return FakeStored(
        planning_updated_at=datetime(
            2026,
            9,
            6,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        notification_sent_at=None,
    )


def test_sends_and_marks_notification_once() -> None:
    athlete_profile_id = uuid4()
    user_id = uuid4()
    stored = _ready_stored()
    repository = FakeRepository(stored)
    reader = FakeSessionReader(
        statuses=("synced", None),
    )
    push = FakePush()

    service = WeeklyDebriefNotificationService(
        debrief_repository=repository,
        training_session_reader=reader,
        push_service=push,
        user_id_resolver=lambda _: user_id,
        now=lambda: datetime(
            2026,
            9,
            6,
            19,
            30,
            tzinfo=timezone.utc,
        ),
    )

    first = service.execute(
        athlete_profile_id=athlete_profile_id,
        week_start=WEEK_START,
    )

    second = service.execute(
        athlete_profile_id=athlete_profile_id,
        week_start=WEEK_START,
    )

    assert (
        first.status
        is WeeklyDebriefNotificationStatus.SENT
    )
    assert (
        second.status
        is WeeklyDebriefNotificationStatus.ALREADY_SENT
    )
    assert len(push.calls) == 1
    assert len(repository.mark_calls) == 1
    assert (
        "synchronisé avec Intervals.icu"
        in push.calls[0]["body"]
    )


def test_not_ready_before_planning_update() -> None:
    stored = FakeStored(
        planning_updated_at=None,
        notification_sent_at=None,
    )
    push = FakePush()

    service = WeeklyDebriefNotificationService(
        debrief_repository=FakeRepository(stored),
        training_session_reader=FakeSessionReader(),
        push_service=push,
        user_id_resolver=lambda _: uuid4(),
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        week_start=WEEK_START,
    )

    assert (
        result.status
        is WeeklyDebriefNotificationStatus.NOT_READY
    )
    assert push.calls == []


def test_reports_incomplete_intervals_sync() -> None:
    push = FakePush()

    service = WeeklyDebriefNotificationService(
        debrief_repository=FakeRepository(
            _ready_stored()
        ),
        training_session_reader=FakeSessionReader(
            statuses=("synced", "failed"),
        ),
        push_service=push,
        user_id_resolver=lambda _: uuid4(),
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        week_start=WEEK_START,
    )

    assert (
        result.status
        is WeeklyDebriefNotificationStatus.SENT
    )
    assert result.sync_incomplete is True
    assert (
        "n'ont pas pu être synchronisées"
        in push.calls[0]["body"]
    )


def test_push_failure_is_retryable() -> None:
    stored = _ready_stored()
    repository = FakeRepository(stored)

    service = WeeklyDebriefNotificationService(
        debrief_repository=repository,
        training_session_reader=FakeSessionReader(),
        push_service=FakePush(failed=1),
        user_id_resolver=lambda _: uuid4(),
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        week_start=WEEK_START,
    )

    assert (
        result.status
        is WeeklyDebriefNotificationStatus.FAILED
    )
    assert repository.mark_calls == []
    assert stored.notification_sent_at is None

def test_zero_delivery_is_retryable() -> None:
    stored = _ready_stored()
    repository = FakeRepository(stored)

    service = WeeklyDebriefNotificationService(
        debrief_repository=repository,
        training_session_reader=FakeSessionReader(),
        push_service=FakePush(
            sent=0,
            failed=0,
            removed=1,
        ),
        user_id_resolver=lambda _: uuid4(),
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        week_start=WEEK_START,
    )

    assert (
        result.status
        is WeeklyDebriefNotificationStatus.NO_RECIPIENT
    )
    assert repository.mark_calls == []
    assert stored.notification_sent_at is None

