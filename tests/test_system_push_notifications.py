from dataclasses import dataclass

from opencoach.services.push_notification import (
    PushNotificationService,
)


@dataclass
class FakeSubscription:
    endpoint: str
    p256dh: str = "p256dh"
    auth: str = "auth"
    badge_count: int = 0
    system_notifications_enabled: bool = True
    system_sync_errors_enabled: bool = True
    system_backup_errors_enabled: bool = True


class FakeRepository:
    def __init__(
        self,
        subscriptions,
    ):
        self.subscriptions = subscriptions
        self.incremented = []
        self.deleted = []

    def list_all(
        self,
    ):
        return self.subscriptions

    def list_for_user(
        self,
        user_id,
    ):
        return self.subscriptions

    def increment_badge(
        self,
        endpoint,
    ):
        self.incremented.append(
            endpoint
        )

    def delete_by_endpoint(
        self,
        endpoint,
    ):
        self.deleted.append(
            endpoint
        )


class DummySession:
    pass


def create_service(
    subscriptions,
):
    service = PushNotificationService(
        DummySession()
    )

    service.repository = FakeRepository(
        subscriptions
    )

    return service


def configure_push(
    monkeypatch,
):
    monkeypatch.setenv(
        "OPENCOACH_VAPID_PRIVATE_KEY",
        "private-key",
    )

    monkeypatch.setenv(
        "OPENCOACH_VAPID_SUBJECT",
        "mailto:test@opencoach.local",
    )


def test_sync_error_sends_only_to_enabled_devices(
    monkeypatch,
):
    configure_push(
        monkeypatch
    )

    enabled = FakeSubscription(
        endpoint="enabled",
    )

    disabled_sync = FakeSubscription(
        endpoint="disabled-sync",
        system_sync_errors_enabled=False,
    )

    disabled_system = FakeSubscription(
        endpoint="disabled-system",
        system_notifications_enabled=False,
    )

    service = create_service([
        enabled,
        disabled_sync,
        disabled_system,
    ])

    sent = []

    monkeypatch.setattr(
        service,
        "_send_one",
        lambda **kwargs:
            sent.append(
                kwargs[
                    "subscription"
                ].endpoint
            ),
    )

    report = (
        service.send_system_sync_error(
            user_id="test-user-id",
            title="Test",
            body="Erreur sync",
        )
    )

    assert sent == [
        "enabled"
    ]

    assert report.sent == 1
    assert report.failed == 0
    assert report.removed == 0


def test_backup_error_sends_only_to_enabled_devices(
    monkeypatch,
):
    configure_push(
        monkeypatch
    )

    enabled = FakeSubscription(
        endpoint="enabled",
    )

    disabled_backup = FakeSubscription(
        endpoint="disabled-backup",
        system_backup_errors_enabled=False,
    )

    disabled_system = FakeSubscription(
        endpoint="disabled-system",
        system_notifications_enabled=False,
    )

    service = create_service([
        enabled,
        disabled_backup,
        disabled_system,
    ])

    sent = []

    monkeypatch.setattr(
        service,
        "_send_one",
        lambda **kwargs:
            sent.append(
                kwargs[
                    "subscription"
                ].endpoint
            ),
    )

    report = (
        service.send_system_backup_error(
            title="Test",
            body="Erreur backup",
        )
    )

    assert sent == [
        "enabled"
    ]

    assert report.sent == 1
    assert report.failed == 0
    assert report.removed == 0


def test_sync_error_with_no_eligible_device(
    monkeypatch,
):
    configure_push(
        monkeypatch
    )

    subscription = FakeSubscription(
        endpoint="disabled",
        system_sync_errors_enabled=False,
    )

    service = create_service([
        subscription
    ])

    called = []

    monkeypatch.setattr(
        service,
        "_send_one",
        lambda **kwargs:
            called.append(
                kwargs
            ),
    )

    report = (
        service.send_system_sync_error(
            user_id="test-user-id",
            title="Test",
            body="Erreur",
        )
    )

    assert called == []

    assert report.sent == 0
    assert report.failed == 0
    assert report.removed == 0


def test_backup_error_with_no_eligible_device(
    monkeypatch,
):
    configure_push(
        monkeypatch
    )

    subscription = FakeSubscription(
        endpoint="disabled",
        system_backup_errors_enabled=False,
    )

    service = create_service([
        subscription
    ])

    called = []

    monkeypatch.setattr(
        service,
        "_send_one",
        lambda **kwargs:
            called.append(
                kwargs
            ),
    )

    report = (
        service.send_system_backup_error(
            title="Test",
            body="Erreur",
        )
    )

    assert called == []

    assert report.sent == 0
    assert report.failed == 0
    assert report.removed == 0
