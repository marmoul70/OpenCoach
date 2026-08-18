from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opencoach.database.base import Base


if TYPE_CHECKING:
    from opencoach.database.models.athlete_profile import (
        AthleteProfile,
    )


class IntegrationConnection(Base):
    """Connexion configurée vers un service externe."""

    __tablename__ = "integration_connections"

    __table_args__ = (
        UniqueConstraint(
            "athlete_profile_id",
            "provider",
            name="uq_integration_connection_profile_provider",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    athlete_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "athlete_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    config: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    encrypted_secret: Mapped[bytes | None] = mapped_column(
        LargeBinary,
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

    athlete_profile: Mapped["AthleteProfile"] = relationship(
        back_populates="integration_connections",
    )
