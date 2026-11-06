from __future__ import annotations

import json
import os
from dataclasses import dataclass
from uuid import UUID

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import PushSubscription, User
from opencoach.database.repositories.sql_notification import (
    SqlNotificationRepository,
)
from opencoach.database.repositories.sql_push_subscription import (
    SqlPushSubscriptionRepository,
)


@dataclass(frozen=True)
class PushDeliveryReport:
    sent: int
    failed: int
    removed: int
    persisted: bool = False


class PushConfigurationError(RuntimeError):
    """Configuration Web Push OpenCoach invalide."""


class PushNotificationService:
    """Persiste les événements puis tente leur livraison Web Push."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = SqlPushSubscriptionRepository(session)
        self.notification_repository = SqlNotificationRepository(session)

    def _active_user_ids(self, fallback: set[UUID]) -> set[UUID]:
        # Les notifications système globales doivent aussi exister pour
        # les comptes actifs qui n'ont pas encore enregistré d'appareil Push.
        if not hasattr(self.session, "scalars"):
            return fallback
        return set(
            self.session.scalars(
                select(User.id).where(User.active.is_(True))
            )
        )

    def _persist_for_users(
        self,
        *,
        user_ids: set[UUID],
        title: str,
        body: str,
        url: str,
        category: str,
        severity: str = "info",
    ) -> None:
        # Persistance indépendante du succès Push et des préférences par appareil.
        for user_id in user_ids:
            self.notification_repository.create(
                user_id=user_id,
                title=title,
                body=body,
                category=category,
                severity=severity,
                url=url,
            )

    def send_to_all(
        self,
        *,
        title: str,
        body: str,
        url: str = "/",
    ) -> PushDeliveryReport:
        subscriptions = self.repository.list_all()
        user_ids = self._active_user_ids(
            {subscription.user_id for subscription in subscriptions}
        )
        self._persist_for_users(
            user_ids=user_ids,
            title=title,
            body=body,
            url=url,
            category="system",
        )
        return self._send_to_subscriptions(
            persisted=bool(user_ids),
            subscriptions=subscriptions,
            title=title,
            body=body,
            url=url,
        )

    def send_system_sync_error(
        self,
        *,
        user_id: UUID,
        title: str,
        body: str,
        url: str = "/settings",
    ) -> PushDeliveryReport:
        self._persist_for_users(
            user_ids={user_id},
            title=title,
            body=body,
            url=url,
            category="system",
            severity="error",
        )
        subscriptions = [
            subscription
            for subscription in self.repository.list_for_user(user_id)
            if (
                subscription.system_notifications_enabled
                and subscription.system_sync_errors_enabled
            )
        ]
        return self._send_to_subscriptions(
            subscriptions=subscriptions,
            title=title,
            body=body,
            url=url,
            persisted=True,
        )

    def send_system_backup_error(
        self,
        *,
        title: str,
        body: str,
        url: str = "/settings",
    ) -> PushDeliveryReport:
        all_subscriptions = self.repository.list_all()
        user_ids = self._active_user_ids(
            {subscription.user_id for subscription in all_subscriptions}
        )
        self._persist_for_users(
            user_ids=user_ids,
            title=title,
            body=body,
            url=url,
            category="system",
            severity="error",
        )
        subscriptions = [
            subscription
            for subscription in all_subscriptions
            if (
                subscription.system_notifications_enabled
                and subscription.system_backup_errors_enabled
            )
        ]
        return self._send_to_subscriptions(
            subscriptions=subscriptions,
            title=title,
            body=body,
            url=url,
            persisted=bool(user_ids),
        )

    def send_weekly_debrief_notification(
        self,
        *,
        user_id: UUID,
        title: str,
        body: str,
        url: str = "/training",
    ) -> PushDeliveryReport:
        self._persist_for_users(
            user_ids={user_id},
            title=title,
            body=body,
            url=url,
            category="coaching",
        )
        subscriptions = [
            subscription
            for subscription in self.repository.list_for_user(user_id)
            if subscription.system_notifications_enabled
        ]
        try:
            return self._send_to_subscriptions(
                subscriptions=subscriptions,
                title=title,
                body=body,
                url=url,
                persisted=True,
            )
        except PushConfigurationError:
            # L'événement est déjà en base : une configuration VAPID
            # absente ne doit pas déclencher de doublons au prochain cron.
            return PushDeliveryReport(
                sent=0,
                failed=len(subscriptions),
                removed=0,
                persisted=True,
            )

    def send_training_reminder(
        self,
        *,
        user_id: UUID,
        title: str,
        body: str,
        url: str,
    ) -> PushDeliveryReport:
        self._persist_for_users(
            user_ids={user_id},
            title=title,
            body=body,
            url=url,
            category="training",
        )
        subscriptions = [
            subscription
            for subscription in self.repository.list_for_user(user_id)
            if subscription.training_reminder_enabled
        ]
        return self._send_to_subscriptions(
            subscriptions=subscriptions,
            title=title,
            body=body,
            url=url,
            persisted=True,
        )

    def _send_to_subscriptions(
        self,
        *,
        subscriptions: list[PushSubscription],
        title: str,
        body: str,
        url: str,
        persisted: bool = False,
    ) -> PushDeliveryReport:
        private_key = os.getenv(
            "OPENCOACH_VAPID_PRIVATE_KEY",
            "",
        ).strip()
        subject = os.getenv(
            "OPENCOACH_VAPID_SUBJECT",
            "",
        ).strip()

        if not subscriptions:
            return PushDeliveryReport(
                sent=0,
                failed=0,
                removed=0,
                persisted=persisted,
            )

        if not private_key:
            raise PushConfigurationError(
                "OPENCOACH_VAPID_PRIVATE_KEY n'est pas configurée."
            )
        if not subject:
            raise PushConfigurationError(
                "OPENCOACH_VAPID_SUBJECT n'est pas configuré."
            )

        sent = 0
        failed = 0
        removed = 0
        for subscription in subscriptions:
            try:
                badge_count = subscription.badge_count + 1
                payload = json.dumps(
                    {
                        "title": title,
                        "body": body,
                        "url": url,
                        "badge": badge_count,
                    },
                    ensure_ascii=False,
                )
                self._send_one(
                    subscription=subscription,
                    payload=payload,
                    private_key=private_key,
                    subject=subject,
                )
                self.repository.increment_badge(subscription.endpoint)
                sent += 1
            except WebPushException as exc:
                status_code = (
                    exc.response.status_code
                    if exc.response is not None
                    else None
                )
                if status_code in {404, 410}:
                    self.repository.delete_by_endpoint(subscription.endpoint)
                    removed += 1
                    continue
                failed += 1

        return PushDeliveryReport(
            sent=sent,
            failed=failed,
            removed=removed,
            persisted=persisted,
        )

    @staticmethod
    def _send_one(
        *,
        subscription: PushSubscription,
        payload: str,
        private_key: str,
        subject: str,
    ) -> None:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=payload,
            vapid_private_key=private_key,
            vapid_claims={"sub": subject},
            timeout=15,
        )
