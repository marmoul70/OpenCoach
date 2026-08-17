from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opencoach.database.base import Base


class Shoe(Base):
    """Chaussure de course appartenant à un profil sportif."""

    __tablename__ = "athlete_shoes"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    athlete_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("athlete_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    distance_km: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    max_distance_km: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    athlete_profile: Mapped["AthleteProfile"] = relationship(
        back_populates="shoes",
    )
