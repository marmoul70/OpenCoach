"""Add COROS scheduled workout synchronization metadata.

Revision ID: a4d6f8b2c1e3
Revises: f6a91c2d4e80
Create Date: 2026-11-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4d6f8b2c1e3"
down_revision: Union[str, Sequence[str], None] = "f6a91c2d4e80"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "training_sessions",
        sa.Column("coros_workout_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "training_sessions",
        sa.Column("coros_sync_status", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "training_sessions",
        sa.Column("coros_sync_started_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "training_sessions",
        sa.Column("coros_last_synced_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "training_sessions",
        sa.Column("coros_payload_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "training_sessions",
        sa.Column("coros_sync_error", sa.String(length=2000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("training_sessions", "coros_sync_error")
    op.drop_column("training_sessions", "coros_payload_hash")
    op.drop_column("training_sessions", "coros_last_synced_at")
    op.drop_column("training_sessions", "coros_sync_started_at")
    op.drop_column("training_sessions", "coros_sync_status")
    op.drop_column("training_sessions", "coros_workout_id")
