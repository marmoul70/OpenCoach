"""add per-user AI coach preferences

Revision ID: c8e4a1b7d203
Revises: f6a91c2d4e80
Create Date: 2026-11-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8e4a1b7d203"
down_revision: Union[str, Sequence[str], None] = "f6a91c2d4e80"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_coach_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("personality", sa.String(length=24), nullable=False),
        sa.Column("firmness", sa.Integer(), nullable=False),
        sa.Column("motivation", sa.Integer(), nullable=False),
        sa.Column("response_style", sa.String(length=24), nullable=False),
        sa.Column("custom_prompt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_coach_preferences_user_id",
        "ai_coach_preferences",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_coach_preferences_user_id", table_name="ai_coach_preferences")
    op.drop_table("ai_coach_preferences")
