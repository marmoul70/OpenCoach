"""Add user auth credentials.

Revision ID: e5b0c16035cb
Revises: 23d2eab8e4b6
"""

from alembic import op
import sqlalchemy as sa


revision = "e5b0c16035cb"
down_revision = "23d2eab8e4b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "username",
            sa.String(length=32),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "pin_hash",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "pin_salt",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.create_index(
        op.f(
            "ix_users_username"
        ),
        "users",
        [
            "username",
        ],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_users_username"
        ),
        table_name="users",
    )

    op.drop_column(
        "users",
        "pin_salt",
    )

    op.drop_column(
        "users",
        "pin_hash",
    )

    op.drop_column(
        "users",
        "username",
    )
