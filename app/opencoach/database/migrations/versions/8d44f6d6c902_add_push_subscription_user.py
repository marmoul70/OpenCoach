"""Attach push subscriptions to users.

Revision ID: 8d44f6d6c902
Revises: e5b0c16035cb
"""

from alembic import op
import sqlalchemy as sa


revision = "8d44f6d6c902"
down_revision = "e5b0c16035cb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "push_subscriptions",
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    user_id = connection.execute(
        sa.text(
            """
            SELECT id
            FROM users
            WHERE lower(username) = :username
            LIMIT 1
            """
        ),
        {
            "username": "ys001",
        },
    ).scalar()

    if user_id is None:
        raise RuntimeError(
            "Utilisateur ys001 introuvable : "
            "migration Push annulée."
        )

    connection.execute(
        sa.text(
            """
            UPDATE push_subscriptions
            SET user_id = :user_id
            WHERE user_id IS NULL
            """
        ),
        {
            "user_id": user_id,
        },
    )

    with op.batch_alter_table(
        "push_subscriptions"
    ) as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )

        batch_op.create_foreign_key(
            "fk_push_subscriptions_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

        batch_op.create_index(
            "ix_push_subscriptions_user_id",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "push_subscriptions"
    ) as batch_op:
        batch_op.drop_index(
            "ix_push_subscriptions_user_id"
        )

        batch_op.drop_constraint(
            "fk_push_subscriptions_user_id_users",
            type_="foreignkey",
        )

        batch_op.drop_column(
            "user_id"
        )
