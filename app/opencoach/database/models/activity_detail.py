"""Persistance SQL des données détaillées d'une activité."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from opencoach.database.base import Base


class ActivityDetail(Base):
    """Métadonnées détaillées associées à une activité."""

    __tablename__ = "activity_details"

    activity_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "activities.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    provider_lap_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    interval_summary: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    intervals: Mapped[list["ActivityInterval"]] = relationship(
        back_populates="detail",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    streams: Mapped[list["ActivityStream"]] = relationship(
        back_populates="detail",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ActivityInterval(Base):
    """Intervalle fournisseur persisté pour une activité."""

    __tablename__ = "activity_intervals"

    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            "position",
            name="uq_activity_intervals_position",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    activity_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "activity_details.activity_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    provider_interval_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    interval_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    start_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    start_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    distance_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    moving_time_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    elapsed_time_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    average_speed_mps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_heart_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_heart_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_cadence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    elevation_gain_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    training_load: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    detail: Mapped[ActivityDetail] = relationship(
        back_populates="intervals",
    )


class ActivityStream(Base):
    """Stream temporel compact stocké sous forme JSON."""

    __tablename__ = "activity_streams"

    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            "stream_type",
            name="uq_activity_streams_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    activity_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "activity_details.activity_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    stream_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    data: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    detail: Mapped[ActivityDetail] = relationship(
        back_populates="streams",
    )
