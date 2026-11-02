"""add database-backed COROS sync locks

Revision ID: d1e2f3a4b5c6
Revises: c0a1b2c3d4e5
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coros_sync_locks",
        sa.Column("athlete_profile_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("acquired_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("athlete_profile_id"),
        sa.UniqueConstraint(
            "athlete_profile_id",
            name="uq_coros_sync_lock_profile",
        ),
    )


def downgrade() -> None:
    op.drop_table("coros_sync_locks")
