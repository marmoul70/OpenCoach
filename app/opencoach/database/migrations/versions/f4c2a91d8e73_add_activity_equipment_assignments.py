"""add activity equipment assignments

Revision ID: f4c2a91d8e73
Revises: 8c366e314170
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "f4c2a91d8e73"
down_revision: str | None = "8c366e314170"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "activity_equipment_assignments",
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
            "activity_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "shoe_id",
            sa.String(),
            nullable=True,
        ),
        sa.Column(
            "bike_id",
            sa.String(),
            nullable=True,
        ),
        sa.Column(
            "distance_km",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "assignment_source",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.CheckConstraint(
            """
            (
                shoe_id IS NOT NULL
                AND bike_id IS NULL
            )
            OR
            (
                shoe_id IS NULL
                AND bike_id IS NOT NULL
            )
            """,
            name=(
                "ck_activity_equipment_"
                "exactly_one_equipment"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["activities.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["athlete_profile_id"],
            ["athlete_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["bike_id"],
            ["athlete_bikes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["shoe_id"],
            ["athlete_shoes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "activity_id",
            name=(
                "uq_activity_equipment_"
                "assignment_activity"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_activity_equipment_assignments_"
            "athlete_profile_id"
        ),
        "activity_equipment_assignments",
        ["athlete_profile_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_activity_equipment_assignments_activity_id"
        ),
        "activity_equipment_assignments",
        ["activity_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_activity_equipment_assignments_shoe_id"
        ),
        "activity_equipment_assignments",
        ["shoe_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_activity_equipment_assignments_bike_id"
        ),
        "activity_equipment_assignments",
        ["bike_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_activity_equipment_assignments_bike_id"
        ),
        table_name="activity_equipment_assignments",
    )

    op.drop_index(
        op.f(
            "ix_activity_equipment_assignments_shoe_id"
        ),
        table_name="activity_equipment_assignments",
    )

    op.drop_index(
        op.f(
            "ix_activity_equipment_assignments_activity_id"
        ),
        table_name="activity_equipment_assignments",
    )

    op.drop_index(
        op.f(
            "ix_activity_equipment_assignments_"
            "athlete_profile_id"
        ),
        table_name="activity_equipment_assignments",
    )

    op.drop_table(
        "activity_equipment_assignments",
    )
