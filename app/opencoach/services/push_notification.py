from __future__ import annotations

import json
import os
from dataclasses import dataclass

from pywebpush import (
    WebPushException,
    webpush,
)
from sqlalchemy.orm import Session

from opencoach.database.models import (
    PushSubscription,
)
from opencoach.database.repositories.sql_push_subscription import (
    SqlPushSubscriptionRepository,
)


@dataclass(frozen=True)
class PushDeliveryReport:
    sent: int
    failed: int
    removed: int


class PushConfigurationError(
    RuntimeError
):
    """Configuration Web Push OpenCoach invalide."""


class PushNotificationService:
    """Envoie les notifications Web Push OpenCoach."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.repository = (
            SqlPushSubscriptionRepository(
                session
            )
        )

    def send_to_all(
        self,
        *,
        title: str,
        body: str,
        url: str = "/",
    ) -> PushDeliveryReport:
        private_key = os.getenv(
            "OPENCOACH_VAPID_PRIVATE_KEY",
            "",
        ).strip()

        subject = os.getenv(
            "OPENCOACH_VAPID_SUBJECT",
            "",
        ).strip()

        if not private_key:
            raise PushConfigurationError(
                "OPENCOACH_VAPID_PRIVATE_KEY "
                "n'est pas configurée."
            )

        if not subject:
            raise PushConfigurationError(
                "OPENCOACH_VAPID_SUBJECT "
                "n'est pas configuré."
            )

        subscriptions = (
            self.repository.list_all()
        )

        payload = json.dumps(
            {
                "title": title,
                "body": body,
                "url": url,
            },
            ensure_ascii=False,
        )

        sent = 0
        failed = 0
        removed = 0

        for subscription in subscriptions:
            try:
                self._send_one(
                    subscription=subscription,
                    payload=payload,
                    private_key=private_key,
                    subject=subject,
                )

                sent += 1

            except WebPushException as exc:
                status_code = (
                    exc.response.status_code
                    if exc.response is not None
                    else None
                )

                if status_code in {
                    404,
                    410,
                }:
                    self.repository.delete_by_endpoint(
                        subscription.endpoint
                    )

                    removed += 1
                    continue

                failed += 1

        return PushDeliveryReport(
            sent=sent,
            failed=failed,
            removed=removed,
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
                "endpoint":
                    subscription.endpoint,
                "keys": {
                    "p256dh":
                        subscription.p256dh,
                    "auth":
                        subscription.auth,
                },
            },
            data=payload,
            vapid_private_key=private_key,
            vapid_claims={
                "sub": subject,
            },
            timeout=15,
        )
