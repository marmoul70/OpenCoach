from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import Notification, User
from opencoach.database.repositories.sql_notification import (
    SqlNotificationRepository,
)
from opencoach.services.push_notification import PushNotificationService


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return factory()


def create_user(session, email):
    user = User(
        id=uuid4(),
        email=email,
        username=email.split("@")[0],
        active=True,
    )
    session.add(user)
    session.commit()
    return user


def test_notifications_are_isolated_and_unread_count_is_correct():
    session = create_session()
    try:
        user_a = create_user(session, "a@example.test")
        user_b = create_user(session, "b@example.test")
        repository = SqlNotificationRepository(session)

        first = repository.create(
            user_id=user_a.id,
            title="Erreur COROS",
            body="La synchronisation a échoué.",
            category="system",
            severity="error",
            url="/settings",
        )
        repository.create(
            user_id=user_a.id,
            title="Séance demain",
            body="Sortie facile prévue.",
            category="training",
        )
        repository.create(
            user_id=user_b.id,
            title="Privé",
            body="Notification d'un autre compte.",
            category="system",
        )

        items, total = repository.list_for_user(user_a.id)
        assert total == 2
        assert len(items) == 2
        assert repository.unread_count(user_a.id) == 2

        assert repository.mark_read(first.id, user_a.id) is True
        assert repository.mark_read(first.id, user_a.id) is True
        assert repository.unread_count(user_a.id) == 1

        assert repository.mark_read(first.id, user_b.id) is False
        assert repository.delete_one(first.id, user_b.id) is False
        assert repository.unread_count(user_b.id) == 1
    finally:
        session.close()


def test_mark_all_read_and_delete_all_are_scoped_to_user():
    session = create_session()
    try:
        user_a = create_user(session, "a@example.test")
        user_b = create_user(session, "b@example.test")
        repository = SqlNotificationRepository(session)

        for user in (user_a, user_b):
            repository.create(
                user_id=user.id,
                title="Notification",
                body="Contenu",
                category="system",
            )

        assert repository.mark_all_read(user_a.id) == 1
        assert repository.unread_count(user_a.id) == 0
        assert repository.unread_count(user_b.id) == 1

        assert repository.delete_all(user_a.id) == 1
        assert repository.list_for_user(user_a.id)[1] == 0
        assert repository.list_for_user(user_b.id)[1] == 1
    finally:
        session.close()


def test_unread_filter_and_pagination():
    session = create_session()
    try:
        user = create_user(session, "a@example.test")
        repository = SqlNotificationRepository(session)
        created = []
        for index in range(4):
            created.append(
                repository.create(
                    user_id=user.id,
                    title=f"Notification {index}",
                    body="Contenu",
                    category="system",
                )
            )

        repository.mark_read(created[0].id, user.id)
        unread, unread_total = repository.list_for_user(
            user.id,
            unread_only=True,
            limit=2,
        )
        page, total = repository.list_for_user(
            user.id,
            limit=2,
            offset=1,
        )

        assert unread_total == 3
        assert len(unread) == 2
        assert total == 4
        assert len(page) == 2
    finally:
        session.close()



def test_global_backup_notification_is_persisted_for_active_users_without_push_devices():
    session = create_session()
    try:
        user_a = create_user(session, "a@example.test")
        user_b = create_user(session, "b@example.test")
        report = PushNotificationService(session).send_system_backup_error(
            title="Sauvegarde OpenCoach",
            body="La sauvegarde a échoué.",
        )

        assert report.sent == 0
        assert report.persisted is True
        repository = SqlNotificationRepository(session)
        assert repository.list_for_user(user_a.id)[1] == 1
        assert repository.list_for_user(user_b.id)[1] == 1
    finally:
        session.close()


def test_notification_migration_keeps_a_single_alembic_head():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["f6a91c2d4e80"]
