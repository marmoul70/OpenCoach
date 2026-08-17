from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import AthleteProfile as AthleteProfileModel
from opencoach.database.models import User
from opencoach.database.repositories import SqlProfileRepository
from opencoach.models import AthleteProfile, Bike, Shoe, Watch

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

def test_sql_repository_persists_complete_profile() -> None:
    db = create_session()

    try:
        repository = SqlProfileRepository(db)

        profile = AthleteProfile()

        profile.identity.first_name = "Seby"
        profile.identity.last_name = "Yvinec"
        profile.identity.birth_date = "1985-01-15"
        profile.identity.gender = "male"
        profile.identity.avatar = "avatar.png"

        profile.body.height_cm = 185
        profile.body.weight_kg = 85

        profile.physiology.max_heart_rate = 194
        profile.physiology.resting_heart_rate = 41
        profile.physiology.vma = 15
        profile.physiology.threshold_heart_rate_1 = 155
        profile.physiology.threshold_heart_rate_2 = 170

        profile.training.weekly_sessions = 4
        profile.training.weekly_duration_minutes = 300
        profile.training.weekly_distance_km = 50
        profile.training.available_days = [1, 3, 5, 6]
        profile.training.fatigue_threshold = 0.8
        profile.training.experience = "advanced"

        profile.location.name = "Belfort"
        profile.location.latitude = 47.6397
        profile.location.longitude = 6.8638

        profile.nutrition.carbohydrates_per_hour = 60
        profile.nutrition.fluids_per_hour = 750
        profile.nutrition.sodium_per_hour = 500

        repository.save_profile(profile)

        loaded = repository.get_profile()

        assert loaded.identity.first_name == "Seby"
        assert loaded.identity.last_name == "Yvinec"
        assert loaded.identity.birth_date == "1985-01-15"
        assert loaded.identity.avatar == "avatar.png"

        assert loaded.body.height_cm == 185
        assert loaded.body.weight_kg == 85

        assert loaded.physiology.max_heart_rate == 194
        assert loaded.physiology.resting_heart_rate == 41
        assert loaded.physiology.vma == 15
        assert loaded.physiology.threshold_heart_rate_1 == 155
        assert loaded.physiology.threshold_heart_rate_2 == 170

        assert loaded.training.weekly_sessions == 4
        assert loaded.training.weekly_duration_minutes == 300
        assert loaded.training.weekly_distance_km == 50
        assert loaded.training.available_days == [1, 3, 5, 6]
        assert loaded.training.fatigue_threshold == 0.8
        assert loaded.training.experience == "advanced"

        assert loaded.location.name == "Belfort"
        assert loaded.location.latitude == 47.6397
        assert loaded.location.longitude == 6.8638

        assert loaded.nutrition.carbohydrates_per_hour == 60
        assert loaded.nutrition.fluids_per_hour == 750
        assert loaded.nutrition.sodium_per_hour == 500
    finally:
        db.close()

def test_sql_repository_persists_equipment() -> None:
    db = create_session()

    try:
        repository = SqlProfileRepository(db)

        profile = AthleteProfile()

        profile.equipment.shoes.append(
            Shoe(
                id="shoe-1",
                brand="ASICS",
                model="Trabuco 13",
                active=True,
                distance_km=250,
                max_distance_km=800,
            )
        )

        profile.equipment.bikes.append(
            Bike(
                id="bike-1",
                brand="Cube",
                model="Nuroad",
                active=True,
                distance_km=1200,
            )
        )

        profile.equipment.watches.append(
            Watch(
                id="watch-1",
                brand="Suunto",
                model="Race 2",
                active=True,
            )
        )

        repository.save_profile(profile)

        loaded = repository.get_profile()

        assert len(loaded.equipment.shoes) == 1
        assert loaded.equipment.shoes[0].id == "shoe-1"
        assert loaded.equipment.shoes[0].brand == "ASICS"
        assert loaded.equipment.shoes[0].model == "Trabuco 13"
        assert loaded.equipment.shoes[0].distance_km == 250
        assert loaded.equipment.shoes[0].max_distance_km == 800

        assert len(loaded.equipment.bikes) == 1
        assert loaded.equipment.bikes[0].id == "bike-1"
        assert loaded.equipment.bikes[0].brand == "Cube"
        assert loaded.equipment.bikes[0].model == "Nuroad"
        assert loaded.equipment.bikes[0].distance_km == 1200

        assert len(loaded.equipment.watches) == 1
        assert loaded.equipment.watches[0].id == "watch-1"
        assert loaded.equipment.watches[0].brand == "Suunto"
        assert loaded.equipment.watches[0].model == "Race 2"

    finally:
        db.close()

def test_sql_repository_rolls_back_when_commit_fails(
    monkeypatch,
) -> None:
    db = create_session()

    try:
        repository = SqlProfileRepository(db)
        profile = AthleteProfile()

        rollback_called = False

        def failing_commit() -> None:
            raise RuntimeError("database failure")

        def tracking_rollback() -> None:
            nonlocal rollback_called
            rollback_called = True

        monkeypatch.setattr(
            db,
            "commit",
            failing_commit,
        )
        monkeypatch.setattr(
            db,
            "rollback",
            tracking_rollback,
        )

        try:
            repository.save_profile(profile)
        except RuntimeError as exc:
            assert str(exc) == "database failure"
        else:
            raise AssertionError(
                "RuntimeError attendu lors du commit."
            )

        assert rollback_called is True
    finally:
        db.close()
