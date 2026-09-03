from sqlalchemy import (
    create_engine,
)
from sqlalchemy.orm import (
    sessionmaker,
)

from opencoach.database.base import (
    Base,
)
from opencoach.database.models import (
    AthleteProfile as AthleteProfileModel,
    User,
)
from opencoach.database.repositories import (
    SqlProfileRepository,
)
from opencoach.models import (
    AthleteProfile,
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
    *,
    username: str,
    email: str,
) -> User:
    user = User(
        username=username,
        email=email,
        active=True,
    )

    db.add(
        user
    )

    db.flush()

    return user


def test_profile_repository_isolates_users():
    db = create_session()

    try:
        user_a = create_user(
            db,
            username="aaa001",
            email="a@example.test",
        )

        user_b = create_user(
            db,
            username="bbb001",
            email="b@example.test",
        )

        repository_a = (
            SqlProfileRepository(
                db,
                user_a.id,
            )
        )

        repository_b = (
            SqlProfileRepository(
                db,
                user_b.id,
            )
        )

        profile_a = AthleteProfile()
        profile_a.identity.first_name = (
            "Alice"
        )

        repository_a.save_profile(
            profile_a
        )

        profile_b = AthleteProfile()
        profile_b.identity.first_name = (
            "Bob"
        )

        repository_b.save_profile(
            profile_b
        )

        loaded_a = (
            repository_a.get_profile()
        )

        loaded_b = (
            repository_b.get_profile()
        )

        assert (
            loaded_a.identity.first_name
            == "Alice"
        )

        assert (
            loaded_b.identity.first_name
            == "Bob"
        )

        database_profiles = (
            db.query(
                AthleteProfileModel
            )
            .all()
        )

        assert len(
            database_profiles
        ) == 2

        assert {
            profile.user_id
            for profile
            in database_profiles
        } == {
            user_a.id,
            user_b.id,
        }

        assert (
            db.query(User).count()
            == 2
        )

    finally:
        db.close()


def test_repository_does_not_create_user():
    db = create_session()

    try:
        from uuid import uuid4

        unknown_user_id = uuid4()

        repository = (
            SqlProfileRepository(
                db,
                unknown_user_id,
            )
        )

        profile = AthleteProfile()

        try:
            repository.save_profile(
                profile
            )
        except Exception:
            pass

        assert (
            db.query(User).count()
            == 0
        )

    finally:
        db.close()
