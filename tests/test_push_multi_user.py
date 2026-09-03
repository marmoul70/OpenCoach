from uuid import uuid4

from sqlalchemy import (
    create_engine,
)
from sqlalchemy.orm import (
    sessionmaker,
)

from opencoach.database.base import Base
from opencoach.database.models import User
from opencoach.database.repositories.sql_push_subscription import (
    SqlPushSubscriptionRepository,
)


def create_session():
    engine = create_engine(
        "sqlite:///:memory:"
    )

    Base.metadata.create_all(
        engine
    )

    factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return factory()


def create_user(
    db,
    email: str,
    username: str,
):
    user = User(
        id=uuid4(),
        email=email,
        username=username,
        active=True,
    )

    db.add(user)
    db.commit()

    return user


def test_push_repository_isolates_users():
    db = create_session()

    try:
        user_a = create_user(
            db,
            "a@example.test",
            "aaa001",
        )

        user_b = create_user(
            db,
            "b@example.test",
            "bbb001",
        )

        repository = (
            SqlPushSubscriptionRepository(
                db
            )
        )

        repository.save(
            user_id=user_a.id,
            endpoint="endpoint-a",
            p256dh="key-a",
            auth="auth-a",
            user_agent="A",
        )

        repository.save(
            user_id=user_b.id,
            endpoint="endpoint-b",
            p256dh="key-b",
            auth="auth-b",
            user_agent="B",
        )

        subscriptions_a = (
            repository.list_for_user(
                user_a.id
            )
        )

        subscriptions_b = (
            repository.list_for_user(
                user_b.id
            )
        )

        assert [
            item.endpoint
            for item in subscriptions_a
        ] == [
            "endpoint-a"
        ]

        assert [
            item.endpoint
            for item in subscriptions_b
        ] == [
            "endpoint-b"
        ]

        assert (
            repository.get_by_endpoint_for_user(
                "endpoint-b",
                user_a.id,
            )
            is None
        )

    finally:
        db.close()


def test_push_delete_cannot_delete_other_user():
    db = create_session()

    try:
        user_a = create_user(
            db,
            "a@example.test",
            "aaa001",
        )

        user_b = create_user(
            db,
            "b@example.test",
            "bbb001",
        )

        repository = (
            SqlPushSubscriptionRepository(
                db
            )
        )

        repository.save(
            user_id=user_b.id,
            endpoint="endpoint-b",
            p256dh="key-b",
            auth="auth-b",
            user_agent="B",
        )

        repository.delete_by_endpoint_for_user(
            "endpoint-b",
            user_a.id,
        )

        assert (
            repository.get_by_endpoint_for_user(
                "endpoint-b",
                user_b.id,
            )
            is not None
        )

    finally:
        db.close()
