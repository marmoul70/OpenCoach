from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from opencoach.database.base import Base


class PushSubscription(Base):
    """Abonnement Web Push d'un appareil OpenCoach."""

    __tablename__ = "push_subscriptions"

    __table_args__ = (
        UniqueConstraint(
            "endpoint",
            name="uq_push_subscription_endpoint",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    endpoint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    p256dh: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    auth: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
