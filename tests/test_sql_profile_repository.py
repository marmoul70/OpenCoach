from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import AthleteProfile as AthleteProfileModel
from opencoach.database.models import User
from sqlalchemy.exc import OperationalError

from opencoach.database.repositories import (
    ProfileRepositoryError,
    SqlProfileRepository,
)
from opencoach.models import AthleteProfile, Bike, Shoe, Watch


TEST_USER_ID = UUID(
    "00000000-0000-0000-0000-000000000001"
)


def create_test_user(
    db,
    *,
    user_id: UUID = TEST_USER_ID,
    email: str = "test@opencoach.local",
    username: str = "test001",
) -> User:
    user = User(
        id=user_id,
        email=email,
        username=username,
    )

    db.add(user)
    db.commit()

    return user

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
        create_test_user(db)

        repository = SqlProfileRepository(db, TEST_USER_ID)

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
        create_test_user(db)

        repository = SqlProfileRepository(db, TEST_USER_ID)

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
        create_test_user(db)

        repository = SqlProfileRepository(db, TEST_USER_ID)

        profile = AthleteProfile()
        profile.identity.first_name = "Test"

        repository.save_profile(profile)

        database_profile = (
            db.query(AthleteProfileModel)
            .one()
        )

        assert database_profile.user is not None
        assert database_profile.user.id == TEST_USER_ID
        assert database_profile.user.athlete_profile is database_profile
    finally:
        db.close()

def test_sql_repository_persists_complete_profile() -> None:
    db = create_session()

    try:
        create_test_user(db)

        repository = SqlProfileRepository(db, TEST_USER_ID)

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
        create_test_user(db)

        repository = SqlProfileRepository(db, TEST_USER_ID)

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
        create_test_user(db)

        repository = SqlProfileRepository(db, TEST_USER_ID)
        profile = AthleteProfile()

        rollback_called = False

        def failing_commit() -> None:
            raise OperationalError(
                "COMMIT",
                {},
                RuntimeError("database failure"),
            )

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
        except ProfileRepositoryError as exc:
            assert str(exc) == "Impossible d'enregistrer le profil."
        else:
            raise AssertionError(
                "ProfileRepositoryError attendue lors du commit."
            )

        assert rollback_called is True
    finally:
        db.close()

def test_sql_repository_uses_selected_user_profile_only() -> None:
    db = create_session()

    try:
        other_user = User(
            email="other@opencoach.local",
        )
        other_profile = AthleteProfileModel(
            user=other_user,
            first_name="Other",
            last_name="User",
        )

        db.add(other_profile)
        db.commit()

        create_test_user(db)

        repository = SqlProfileRepository(db, TEST_USER_ID)

        profile = AthleteProfile()
        profile.identity.first_name = "Local"
        profile.identity.last_name = "User"

        repository.save_profile(profile)

        loaded = repository.get_profile()

        assert loaded.identity.first_name == "Local"
        assert loaded.identity.last_name == "User"

        users = {
            user.email
            for user in db.query(User).all()
        }

        assert users == {
            "other@opencoach.local",
            "test@opencoach.local",
        }

        local_profile = (
            db.query(AthleteProfileModel)
            .join(AthleteProfileModel.user)
            .filter(User.email == "test@opencoach.local")
            .one()
        )

        assert local_profile.first_name == "Local"
        assert local_profile.last_name == "User"

        other_profile = (
            db.query(AthleteProfileModel)
            .join(AthleteProfileModel.user)
            .filter(User.email == "other@opencoach.local")
            .one()
        )

        assert other_profile.first_name == "Other"
        assert other_profile.last_name == "User"
    finally:
        db.close()

def failing_commit() -> None:
    raise OperationalError(
        "COMMIT",
        {},
        RuntimeError("database failure"),
    )

def test_profile_repository_persists_sport_disciplines() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(
        engine
    )

    with Session(engine) as db:
        create_test_user(
            db,
        )

        repository = SqlProfileRepository(
            db,
            TEST_USER_ID,
        )

        profile = AthleteProfile()

        profile.training.sport_disciplines = [
            "road_running",
            "trail_running",
        ]

        repository.save_profile(
            profile
        )

        loaded = repository.get_profile()

        assert (
            loaded.training.sport_disciplines
            == [
                "road_running",
                "trail_running",
            ]
        )


def test_save_profile_preserves_equipment_assignment() -> None:
    """Une sauvegarde du profil conserve les FK matériel existantes."""
    from datetime import datetime, timezone
    from uuid import uuid4

    from opencoach.database.models.activity import (
        Activity as ActivityModel,
    )
    from opencoach.database.models.activity_equipment_assignment import (
        ActivityEquipmentAssignment,
    )
    from opencoach.database.models.shoe import (
        Shoe as ShoeModel,
    )
    from opencoach.database.models.athlete_profile import (
        AthleteProfile as AthleteProfileModel,
    )
    from opencoach.database.repositories.sql_activity_equipment_assignment import (
        SqlActivityEquipmentAssignmentRepository,
    )

    db = create_session()

    try:
        create_test_user(db)

        repository = SqlProfileRepository(
            db,
            TEST_USER_ID,
        )

        profile = AthleteProfile()
        profile.equipment.shoes.append(
            Shoe(
                id="shoe-stable-fk",
                brand="ASICS",
                model="Trabuco",
                active=True,
                category="trail",
                preferred=True,
                distance_km=367.0,
                warning_distance_km=500.0,
                max_distance_km=800.0,
            )
        )

        repository.save_profile(profile)

        database_profile = (
            db.query(AthleteProfileModel)
            .filter(
                AthleteProfileModel.user_id
                == TEST_USER_ID
            )
            .one()
        )

        profile_id = database_profile.id

        activity = ActivityModel(
            id=uuid4(),
            athlete_profile_id=profile_id,
            provider="test",
            provider_activity_id=(
                f"equipment-fk-{uuid4()}"
            ),
            name="Trail FK test",
            sport_type="TrailRun",
            start_at=datetime.now(timezone.utc),
            distance_m=6591.0,
        )

        db.add(activity)
        db.commit()

        assignment_repository = (
            SqlActivityEquipmentAssignmentRepository(
                db
            )
        )

        assignment_repository.assign_shoe(
            athlete_profile_id=profile_id,
            activity_id=activity.id,
            shoe_id="shoe-stable-fk",
            distance_km=6.591,
            assignment_source="automatic",
        )

        db.commit()

        assignment_before = (
            db.query(
                ActivityEquipmentAssignment
            )
            .filter(
                ActivityEquipmentAssignment.activity_id
                == activity.id
            )
            .one()
        )

        assignment_id = assignment_before.id

        # ----------------------------------------------------
        # Sauvegarde normale du profil.
        # La chaussure existe déjà et doit être mise à jour
        # sur place, jamais supprimée/recréée.
        # ----------------------------------------------------

        loaded = repository.get_profile()

        shoe = loaded.equipment.shoes[0]
        shoe.distance_km = 400.0

        repository.save_profile(loaded)

        # ----------------------------------------------------
        # La chaussure SQL existe toujours avec le même ID.
        # ----------------------------------------------------

        database_shoe = (
            db.query(ShoeModel)
            .filter(
                ShoeModel.id
                == "shoe-stable-fk"
            )
            .one()
        )

        assert database_shoe.id == "shoe-stable-fk"
        assert database_shoe.distance_km == 400.0

        # ----------------------------------------------------
        # Et surtout l'affectation FK existe toujours.
        # ----------------------------------------------------

        assignment_after = (
            db.query(
                ActivityEquipmentAssignment
            )
            .filter(
                ActivityEquipmentAssignment.activity_id
                == activity.id
            )
            .one()
        )

        assert assignment_after.id == assignment_id
        assert (
            assignment_after.shoe_id
            == "shoe-stable-fk"
        )
        assert assignment_after.distance_km == 6.591

    finally:
        db.close()



def test_save_profile_archives_used_equipment() -> None:
    """Le matériel utilisé est archivé, jamais supprimé."""
    from datetime import datetime, timezone
    from uuid import uuid4

    from opencoach.database.models.activity import (
        Activity as ActivityModel,
    )
    from opencoach.database.models.activity_equipment_assignment import (
        ActivityEquipmentAssignment,
    )
    from opencoach.database.models.athlete_profile import (
        AthleteProfile as AthleteProfileModel,
    )
    from opencoach.database.models.bike import (
        Bike as BikeModel,
    )
    from opencoach.database.models.shoe import (
        Shoe as ShoeModel,
    )
    from opencoach.database.repositories.sql_activity_equipment_assignment import (
        SqlActivityEquipmentAssignmentRepository,
    )

    db = create_session()

    try:
        create_test_user(db)

        repository = SqlProfileRepository(
            db,
            TEST_USER_ID,
        )

        profile = AthleteProfile()

        profile.equipment.shoes.append(
            Shoe(
                id="shoe-history",
                brand="ASICS",
                model="Trabuco",
                active=True,
                category="trail",
                preferred=True,
                distance_km=367.0,
            )
        )

        profile.equipment.bikes.append(
            Bike(
                id="bike-history",
                brand="Lapierre",
                model="Tecnic",
                active=True,
                category="mtb",
                preferred=True,
                distance_km=350.0,
            )
        )

        repository.save_profile(profile)

        database_profile = (
            db.query(AthleteProfileModel)
            .filter(
                AthleteProfileModel.user_id
                == TEST_USER_ID
            )
            .one()
        )

        profile_id = database_profile.id

        trail_activity = ActivityModel(
            id=uuid4(),
            athlete_profile_id=profile_id,
            provider="test",
            provider_activity_id=(
                f"shoe-history-{uuid4()}"
            ),
            name="Trail historique",
            sport_type="TrailRun",
            start_at=datetime.now(
                timezone.utc
            ),
            distance_m=10000.0,
        )

        bike_activity = ActivityModel(
            id=uuid4(),
            athlete_profile_id=profile_id,
            provider="test",
            provider_activity_id=(
                f"bike-history-{uuid4()}"
            ),
            name="Vélo historique",
            sport_type="Ride",
            start_at=datetime.now(
                timezone.utc
            ),
            distance_m=25000.0,
        )

        db.add_all(
            [
                trail_activity,
                bike_activity,
            ]
        )
        db.commit()

        assignments = (
            SqlActivityEquipmentAssignmentRepository(
                db
            )
        )

        assignments.assign_shoe(
            athlete_profile_id=profile_id,
            activity_id=trail_activity.id,
            shoe_id="shoe-history",
            distance_km=10.0,
            assignment_source="automatic",
        )

        assignments.assign_bike(
            athlete_profile_id=profile_id,
            activity_id=bike_activity.id,
            bike_id="bike-history",
            distance_km=25.0,
            assignment_source="automatic",
        )

        db.commit()

        shoe_assignment_id = (
            db.query(
                ActivityEquipmentAssignment.id
            )
            .filter(
                ActivityEquipmentAssignment.activity_id
                == trail_activity.id
            )
            .scalar()
        )

        bike_assignment_id = (
            db.query(
                ActivityEquipmentAssignment.id
            )
            .filter(
                ActivityEquipmentAssignment.activity_id
                == bike_activity.id
            )
            .scalar()
        )

        loaded = repository.get_profile()

        loaded.equipment.shoes = []
        loaded.equipment.bikes = []

        repository.save_profile(loaded)

        database_shoe = (
            db.query(ShoeModel)
            .filter(
                ShoeModel.id
                == "shoe-history"
            )
            .one()
        )

        database_bike = (
            db.query(BikeModel)
            .filter(
                BikeModel.id
                == "bike-history"
            )
            .one()
        )

        assert database_shoe.active is False
        assert database_shoe.preferred is False

        assert database_bike.active is False
        assert database_bike.preferred is False

        shoe_assignment = (
            db.query(
                ActivityEquipmentAssignment
            )
            .filter(
                ActivityEquipmentAssignment.id
                == shoe_assignment_id
            )
            .one()
        )

        bike_assignment = (
            db.query(
                ActivityEquipmentAssignment
            )
            .filter(
                ActivityEquipmentAssignment.id
                == bike_assignment_id
            )
            .one()
        )

        assert (
            shoe_assignment.shoe_id
            == "shoe-history"
        )

        assert (
            bike_assignment.bike_id
            == "bike-history"
        )

    finally:
        db.close()


def test_save_profile_deletes_unused_equipment() -> None:
    """Le matériel neuf sans historique reste supprimable."""
    from opencoach.database.models.bike import (
        Bike as BikeModel,
    )
    from opencoach.database.models.shoe import (
        Shoe as ShoeModel,
    )

    db = create_session()

    try:
        create_test_user(db)

        repository = SqlProfileRepository(
            db,
            TEST_USER_ID,
        )

        profile = AthleteProfile()

        profile.equipment.shoes.append(
            Shoe(
                id="shoe-unused",
                model="Unused shoe",
                active=True,
                category="road",
                preferred=True,
            )
        )

        profile.equipment.bikes.append(
            Bike(
                id="bike-unused",
                model="Unused bike",
                active=True,
                category="road",
                preferred=True,
            )
        )

        repository.save_profile(profile)

        loaded = repository.get_profile()

        loaded.equipment.shoes = []
        loaded.equipment.bikes = []

        repository.save_profile(loaded)

        assert (
            db.query(ShoeModel)
            .filter(
                ShoeModel.id
                == "shoe-unused"
            )
            .one_or_none()
            is None
        )

        assert (
            db.query(BikeModel)
            .filter(
                BikeModel.id
                == "bike-unused"
            )
            .one_or_none()
            is None
        )

    finally:
        db.close()
