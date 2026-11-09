"""add pending AI athlete profile data proposals

Revision ID: d4f7a9c2e610
Revises: c8e4a1b7d203
Create Date: 2026-11-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f7a9c2e610"
down_revision: Union[str, Sequence[str], None] = "c8e4a1b7d203"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_data_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_profile_id", sa.Uuid(), nullable=False),
        sa.Column("field_key", sa.String(length=80), nullable=False),
        sa.Column("proposed_value", sa.JSON(), nullable=False),
        sa.Column("existing_value", sa.JSON(), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_data_proposals_athlete_profile_id",
        "ai_data_proposals",
        ["athlete_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ai_data_proposals_athlete_profile_id",
        table_name="ai_data_proposals",
    )
    op.drop_table("ai_data_proposals")
