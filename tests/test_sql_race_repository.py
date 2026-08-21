from datetime import (
    date,
    datetime,
    timezone,
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    Activity as ActivityModel,
    AthleteProfile,
    User,
    AthleteProfile,
    User,
)
from opencoach.database.repositories import (
    SqlRaceRepository,
)
from opencoach.models import Race


def create_session():
    engine = create_engine(
        "sqlite:///:memory:",
    )

    Base.metadata.create_all(
        engine
    )

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return SessionLocal()


def create_profile(
    db,
    email: str = "local@opencoach.local",
) -> AthleteProfile:
    user = User(
        email=email,
    )

    profile = AthleteProfile(
        user=user,
        first_name="Test",
        last_name="Athlete",
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def create_race(
    *,
    race_date: date = date(
        2027,
        7,
        10,
    ),
    name: str = "Ultra objectif",
    priority: str = "primary",
    status: str = "planned",
) -> Race:
    return Race(
        id=None,
        date=race_date,
        name=name,
        location="Jura",
        race_type="trail",
        priority=priority,
        distance_km=65.0,
        elevation_gain_m=3100.0,
        target_time_minutes=600,
        status=status,
    )


def test_sql_race_repository_inserts_race() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        saved = repository.save_race(
            profile.id,
            create_race(),
        )

        assert saved.id is not None
        assert saved.name == "Ultra objectif"
        assert saved.priority == "primary"
        assert saved.status == "planned"
        assert saved.distance_km == 65.0
        assert saved.activity_id is None

    finally:
        db.close()


def test_sql_race_repository_gets_race() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        saved = repository.save_race(
            profile.id,
            create_race(),
        )

        result = repository.get_race(
            profile.id,
            saved.id,
        )

        assert result is not None
        assert result.id == saved.id
        assert result.name == saved.name

    finally:
        db.close()


def test_sql_race_repository_lists_period() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    4,
                    10,
                ),
                name="Course 1",
            ),
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    5,
                    10,
                ),
                name="Course 2",
            ),
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    8,
                    10,
                ),
                name="Course 3",
            ),
        )

        races = repository.list_races_between(
            profile.id,
            date(
                2027,
                4,
                1,
            ),
            date(
                2027,
                5,
                31,
            ),
        )

        assert [
            race.name
            for race in races
        ] == [
            "Course 1",
            "Course 2",
        ]

    finally:
        db.close()


def test_sql_race_repository_gets_next_primary() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    4,
                    1,
                ),
                name="Trail entraînement",
                priority="training",
            ),
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    6,
                    1,
                ),
                name="Premier objectif",
                priority="primary",
            ),
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    9,
                    1,
                ),
                name="Deuxième objectif",
                priority="primary",
            ),
        )

        result = repository.get_next_primary_race(
            profile.id,
            date(
                2027,
                3,
                1,
            ),
        )

        assert result is not None
        assert result.name == "Premier objectif"
        assert result.priority == "primary"

    finally:
        db.close()


def test_sql_race_repository_lists_training_before_primary() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    4,
                    15,
                ),
                name="Prépa 1",
                priority="training",
            ),
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    5,
                    20,
                ),
                name="Prépa 2",
                priority="training",
            ),
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    7,
                    10,
                ),
                name="Objectif",
                priority="primary",
            ),
        )

        repository.save_race(
            profile.id,
            create_race(
                race_date=date(
                    2027,
                    8,
                    1,
                ),
                name="Après objectif",
                priority="training",
            ),
        )

        races = (
            repository.list_training_races_before(
                profile.id,
                date(
                    2027,
                    4,
                    1,
                ),
                date(
                    2027,
                    7,
                    10,
                ),
            )
        )

        assert [
            race.name
            for race in races
        ] == [
            "Prépa 1",
            "Prépa 2",
        ]

    finally:
        db.close()


def test_sql_race_repository_isolates_athletes() -> None:
    db = create_session()

    try:
        first_profile = create_profile(
            db,
            "first@opencoach.local",
        )

        second_profile = create_profile(
            db,
            "second@opencoach.local",
        )

        repository = SqlRaceRepository(
            db
        )

        saved = repository.save_race(
            first_profile.id,
            create_race(),
        )

        result = repository.get_race(
            second_profile.id,
            saved.id,
        )

        assert result is None

    finally:
        db.close()


def test_sql_race_repository_deletes_race() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        saved = repository.save_race(
            profile.id,
            create_race(),
        )

        repository.delete_race(
            profile.id,
            saved.id,
        )

        result = repository.get_race(
            profile.id,
            saved.id,
        )

        assert result is None

    finally:
        db.close()

def create_activity(
    db,
    profile: AthleteProfile,
    *,
    provider_activity_id: str = "i-race",
    hour: int = 9,
) -> ActivityModel:
    activity = ActivityModel(
        athlete_profile_id=profile.id,
        provider="intervals",
        provider_activity_id=(
            provider_activity_id
        ),
        name="Course compétition",
        sport_type="Run",
        start_at=datetime(
            2027,
            7,
            10,
            hour - 2,
            0,
            tzinfo=timezone.utc,
        ),
        start_at_local=datetime(
            2027,
            7,
            10,
            hour,
            0,
        ),
        distance_m=64850.0,
        moving_time_seconds=34800,
        elevation_gain_m=3050.0,
        training_load=420.0,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity

def test_sql_race_repository_links_activity() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        race = repository.save_race(
            profile.id,
            create_race(),
        )

        activity = create_activity(
            db,
            profile,
        )

        updated = repository.link_activity(
            profile.id,
            race.id,
            activity.id,
        )

        assert (
            updated.activity_id
            == activity.id
        )

    finally:
        db.close()


def test_sql_race_repository_unlinks_activity() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        race = repository.save_race(
            profile.id,
            create_race(),
        )

        activity = create_activity(
            db,
            profile,
        )

        linked = repository.link_activity(
            profile.id,
            race.id,
            activity.id,
        )

        assert linked.activity_id is not None

        unlinked = repository.link_activity(
            profile.id,
            race.id,
            None,
        )

        assert unlinked.activity_id is None

    finally:
        db.close()


def test_sql_race_repository_lists_candidate_activities() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlRaceRepository(
            db
        )

        first = create_activity(
            db,
            profile,
            provider_activity_id="i-first",
            hour=8,
        )

        second = create_activity(
            db,
            profile,
            provider_activity_id="i-second",
            hour=11,
        )

        activities = (
            repository
            .list_candidate_activities_for_date(
                profile.id,
                date(
                    2027,
                    7,
                    10,
                ),
            )
        )

        assert [
            activity.id
            for activity in activities
        ] == [
            first.id,
            second.id,
        ]

    finally:
        db.close()