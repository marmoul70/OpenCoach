from sqlalchemy import (
    create_engine,
)
from sqlalchemy.orm import (
    sessionmaker,
)

from opencoach.commands.sync_intervals import (
    list_intervals_sync_targets,
)
from opencoach.database.base import (
    Base,
)
from opencoach.database.models import (
    AthleteProfile,
    IntegrationConnection,
    User,
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


def add_user(
    db,
    *,
    email: str,
    username: str,
    active: bool = True,
    intervals: bool = True,
    integration_enabled: bool = True,
    secret: bool = True,
):
    user = User(
        email=email,
        username=username,
        active=active,
    )

    profile = AthleteProfile(
        user=user,
    )

    db.add(
        profile
    )

    db.flush()

    if intervals:
        connection = IntegrationConnection(
            athlete_profile_id=profile.id,
            provider="intervals",
            enabled=integration_enabled,
            config={
                "athlete_id": username,
            },
            encrypted_secret=(
                b"encrypted"
                if secret
                else None
            ),
        )

        db.add(
            connection
        )

    db.commit()

    return (
        user,
        profile,
    )


def test_targets_include_only_eligible_profiles():
    db = create_session()

    try:
        user_a, profile_a = add_user(
            db,
            email="a@example.test",
            username="aaa001",
        )

        user_b, profile_b = add_user(
            db,
            email="b@example.test",
            username="bbb001",
        )

        add_user(
            db,
            email="disabled@example.test",
            username="ddd001",
            integration_enabled=False,
        )

        add_user(
            db,
            email="inactive@example.test",
            username="iii001",
            active=False,
        )

        add_user(
            db,
            email="nosecret@example.test",
            username="nnn001",
            secret=False,
        )

        add_user(
            db,
            email="nointervals@example.test",
            username="xxx001",
            intervals=False,
        )

        targets = (
            list_intervals_sync_targets(
                db
            )
        )

        assert {
            target.user_id
            for target in targets
        } == {
            user_a.id,
            user_b.id,
        }

        assert {
            target.athlete_profile_id
            for target in targets
        } == {
            profile_a.id,
            profile_b.id,
        }

    finally:
        db.close()


def test_targets_are_empty_without_intervals():
    db = create_session()

    try:
        add_user(
            db,
            email="a@example.test",
            username="aaa001",
            intervals=False,
        )

        assert (
            list_intervals_sync_targets(
                db
            )
            == []
        )

    finally:
        db.close()
