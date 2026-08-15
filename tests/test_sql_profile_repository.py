from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import AthleteProfile as AthleteProfileModel
from opencoach.database.models import User
from opencoach.database.repositories import SqlProfileRepository
from opencoach.models import AthleteProfile


def create_session():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return SessionLocal()


def test_sql_repository_creates_default_profile() -> None:
    db = create_session()

    try:
        repository = SqlProfileRepository(db)

        profile = repository.get_profile()

        assert isinstance(profile, AthleteProfile)
        assert profile.identity.first_name == ""
        assert profile.identity.last_name == ""

        assert db.query(User).count() == 1
        assert db.query(AthleteProfileModel).count() == 1
    finally:
        db.close()


def test_sql_repository_saves_and_reads_profile() -> None:
    db = create_session()

    try:
        repository = SqlProfileRepository(db)

        profile = AthleteProfile()
        profile.identity.first_name = "Test"
        profile.identity.last_name = "SQL"
        profile.identity.gender = "male"

        repository.save_profile(profile)

        loaded = repository.get_profile()

        assert loaded.identity.first_name == "Test"
        assert loaded.identity.last_name == "SQL"
        assert loaded.identity.gender == "male"

        assert db.query(User).count() == 1
        assert db.query(AthleteProfileModel).count() == 1
    finally:
        db.close()


def test_sql_repository_keeps_user_and_profile_linked() -> None:
    db = create_session()

    try:
        repository = SqlProfileRepository(db)

        profile = AthleteProfile()
        profile.identity.first_name = "Test"

        repository.save_profile(profile)

        database_profile = (
            db.query(AthleteProfileModel)
            .one()
        )

        assert database_profile.user is not None
        assert database_profile.user.email == "test@opencoach.local"
        assert database_profile.user.athlete_profile is database_profile
    finally:
        db.close()
