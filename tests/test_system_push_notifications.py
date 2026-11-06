from dataclasses import dataclass

from opencoach.services.push_notification import PushNotificationService


@dataclass
class FakeSubscription:
    endpoint: str
    user_id: str = "test-user-id"
    p256dh: str = "p256dh"
    auth: str = "auth"
    badge_count: int = 0
    system_notifications_enabled: bool = True
    system_sync_errors_enabled: bool = True
    system_backup_errors_enabled: bool = True
    training_reminder_enabled: bool = True


class FakeRepository:
    def __init__(self, subscriptions):
        self.subscriptions = subscriptions
        self.incremented = []
        self.deleted = []

    def list_all(self):
        return self.subscriptions

    def list_for_user(self, user_id):
        return [
            subscription
            for subscription in self.subscriptions
            if subscription.user_id == user_id
        ]

    def increment_badge(self, endpoint):
        self.incremented.append(endpoint)

    def delete_by_endpoint(self, endpoint):
        self.deleted.append(endpoint)


class FakeNotificationRepository:
    def __init__(self):
        self.created = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return kwargs


class DummySession:
    pass


def create_service(subscriptions):
    service = PushNotificationService(DummySession())
    service.repository = FakeRepository(subscriptions)
    service.notification_repository = FakeNotificationRepository()
    return service


def configure_push(monkeypatch):
    monkeypatch.setenv("OPENCOACH_VAPID_PRIVATE_KEY", "private-key")
    monkeypatch.setenv(
        "OPENCOACH_VAPID_SUBJECT",
        "mailto:test@opencoach.local",
    )


def capture_sent(service, monkeypatch):
    sent = []
    monkeypatch.setattr(
        service,
        "_send_one",
        lambda **kwargs: sent.append(kwargs["subscription"].endpoint),
    )
    return sent


def test_sync_error_persists_once_and_sends_only_to_enabled_devices(
    monkeypatch,
):
    configure_push(monkeypatch)
    enabled = FakeSubscription(endpoint="enabled")
    disabled_sync = FakeSubscription(
        endpoint="disabled-sync",
        system_sync_errors_enabled=False,
    )
    disabled_system = FakeSubscription(
        endpoint="disabled-system",
        system_notifications_enabled=False,
    )
    service = create_service([enabled, disabled_sync, disabled_system])
    sent = capture_sent(service, monkeypatch)

    report = service.send_system_sync_error(
        user_id="test-user-id",
        title="Test",
        body="Erreur sync",
    )

    assert sent == ["enabled"]
    assert report.sent == 1
    assert report.failed == 0
    assert report.removed == 0
    assert len(service.notification_repository.created) == 1
    assert service.notification_repository.created[0]["category"] == "system"
    assert service.notification_repository.created[0]["severity"] == "error"


def test_backup_error_persists_once_per_user_even_with_multiple_devices(
    monkeypatch,
):
    configure_push(monkeypatch)
    subscriptions = [
        FakeSubscription(endpoint="device-a", user_id="user-a"),
        FakeSubscription(endpoint="device-a2", user_id="user-a"),
        FakeSubscription(endpoint="device-b", user_id="user-b"),
        FakeSubscription(
            endpoint="device-c-disabled",
            user_id="user-c",
            system_backup_errors_enabled=False,
        ),
    ]
    service = create_service(subscriptions)
    sent = capture_sent(service, monkeypatch)

    report = service.send_system_backup_error(
        title="Sauvegarde",
        body="Échec de sauvegarde",
    )

    assert sent == ["device-a", "device-a2", "device-b"]
    assert report.sent == 3
    assert {
        item["user_id"]
        for item in service.notification_repository.created
    } == {"user-a", "user-b", "user-c"}
    assert len(service.notification_repository.created) == 3


def test_sync_error_is_persisted_when_user_has_no_push_device(
    monkeypatch,
):
    service = create_service([])
    report = service.send_system_sync_error(
        user_id="test-user-id",
        title="Test",
        body="Erreur",
    )

    assert report.sent == 0
    assert len(service.notification_repository.created) == 1
    assert service.notification_repository.created[0]["user_id"] == "test-user-id"


def test_training_reminder_is_persisted_even_when_push_preference_disabled(
    monkeypatch,
):
    subscription = FakeSubscription(
        endpoint="disabled-training",
        training_reminder_enabled=False,
    )
    service = create_service([subscription])

    report = service.send_training_reminder(
        user_id="test-user-id",
        title="Séance demain",
        body="Sortie facile",
        url="/training",
    )

    assert report.sent == 0
    assert len(service.notification_repository.created) == 1
    assert service.notification_repository.created[0]["category"] == "training"


def test_weekly_debrief_is_persisted_without_push_devices():
    service = create_service([])

    report = service.send_weekly_debrief_notification(
        user_id="test-user-id",
        title="Programme prêt",
        body="Ta semaine est prête.",
    )

    assert report.sent == 0
    assert len(service.notification_repository.created) == 1
    assert service.notification_repository.created[0]["category"] == "coaching"


def test_no_eligible_sync_device_still_persists_notification(monkeypatch):
    configure_push(monkeypatch)
    subscription = FakeSubscription(
        endpoint="disabled",
        system_sync_errors_enabled=False,
    )
    service = create_service([subscription])
    sent = capture_sent(service, monkeypatch)

    report = service.send_system_sync_error(
        user_id="test-user-id",
        title="Test",
        body="Erreur",
    )

    assert sent == []
    assert report.sent == 0
    assert len(service.notification_repository.created) == 1


def test_push_failure_does_not_remove_persisted_notification(monkeypatch):
    configure_push(monkeypatch)
    subscription = FakeSubscription(endpoint="endpoint")
    service = create_service([subscription])

    def fail_delivery(**kwargs):
        from pywebpush import WebPushException
        raise WebPushException("push unavailable")

    monkeypatch.setattr(service, "_send_one", fail_delivery)
    report = service.send_system_sync_error(
        user_id="test-user-id",
        title="Test",
        body="Erreur",
    )

    assert report.failed == 1
    assert len(service.notification_repository.created) == 1
