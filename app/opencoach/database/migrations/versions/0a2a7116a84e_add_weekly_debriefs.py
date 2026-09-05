"""add weekly debriefs

Revision ID: 0a2a7116a84e
Revises: 8d44f6d6c902

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0a2a7116a84e"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "8d44f6d6c902"
branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None
depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    op.create_table(
        "weekly_debriefs",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "athlete_profile_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "week_start",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "week_end",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "facts_payload",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "verdict",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "adaptation_direction",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "overall_score",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "adherence_score",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "duration_score",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "load_score",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "key_sessions_score",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "intensity_score",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "completion_ratio",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "duration_ratio",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "load_ratio",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "headline",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "analysis",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "strengths",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "warnings",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "adaptation_payload",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "recalculated_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "planning_updated_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "notification_sent_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "athlete_profile_id",
            "week_start",
            name=(
                "uq_weekly_debriefs_"
                "athlete_week_start"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_weekly_debriefs_"
            "athlete_profile_id"
        ),
        "weekly_debriefs",
        ["athlete_profile_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_weekly_debriefs_"
            "week_start"
        ),
        "weekly_debriefs",
        ["week_start"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_weekly_debriefs_"
            "week_start"
        ),
        table_name="weekly_debriefs",
    )

    op.drop_index(
        op.f(
            "ix_weekly_debriefs_"
            "athlete_profile_id"
        ),
        table_name="weekly_debriefs",
    )

    op.drop_table(
        "weekly_debriefs"
    )
