from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    User,
    WellnessDaily,
)
from opencoach.database.repositories import (
    SqlWellnessRepository,
)
from opencoach.models import WellnessDay


def create_session():
    engine = create_engine(
        "sqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return SessionLocal()


def create_profile(
    db,
) -> AthleteProfile:
    user = User(
        email="local@opencoach.local",
    )

    profile = AthleteProfile(
        user=user,
        first_name="Test",
        last_name="Athlete",
    )

    db.add(profile)
    db.commit()

    return profile


def create_wellness_day() -> WellnessDay:
    return WellnessDay(
        provider="intervals",
        date=date(2026, 8, 18),
        fitness_ctl=16.624886,
        fatigue_atl=6.00268,
        ramp_rate=-2.8922691,
        steps=1627,
        resting_hr=46,
        hrv=52.0,
        sleep_seconds=76140,
        sleep_score=77.0,
        sleep_quality=3,
        avg_sleeping_hr=48.0,
        spo2=99.0,
        provider_updated_at=datetime(
            2026,
            8,
            17,
            16,
            15,
            43,
            799000,
            tzinfo=timezone.utc,
        ),
    )


def test_sql_wellness_repository_inserts_day() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        repository.save_wellness_day(
            profile.id,
            create_wellness_day(),
        )

        saved = db.query(WellnessDaily).one()

        assert saved.provider == "intervals"
        assert saved.date == date(2026, 8, 18)
        assert saved.fitness_ctl == 16.624886
        assert saved.fatigue_atl == 6.00268
        assert saved.ramp_rate == -2.8922691
        assert saved.steps == 1627
        assert saved.resting_hr == 46
        assert saved.hrv == 52.0
        assert saved.sleep_seconds == 76140
        assert saved.sleep_score == 77.0
        assert saved.sleep_quality == 3
        assert saved.avg_sleeping_hr == 48.0
        assert saved.spo2 == 99.0

    finally:
        db.close()


def test_sql_wellness_repository_updates_existing_day() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        wellness = create_wellness_day()

        repository.save_wellness_day(
            profile.id,
            wellness,
        )

        wellness.steps = 9000
        wellness.fitness_ctl = 20.0

        repository.save_wellness_day(
            profile.id,
            wellness,
        )

        rows = db.query(WellnessDaily).all()

        assert len(rows) == 1
        assert rows[0].steps == 9000
        assert rows[0].fitness_ctl == 20.0

    finally:
        db.close()


def test_same_date_is_allowed_for_different_providers() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        intervals = create_wellness_day()

        suunto = create_wellness_day()
        suunto.provider = "suunto"

        repository.save_wellness_day(
            profile.id,
            intervals,
        )

        repository.save_wellness_day(
            profile.id,
            suunto,
        )

        rows = db.query(WellnessDaily).all()

        assert len(rows) == 2

        assert {
            row.provider
            for row in rows
        } == {
            "intervals",
            "suunto",
        }

    finally:
        db.close()


def test_sql_wellness_repository_returns_latest_day() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        older = create_wellness_day()
        older.date = date(2026, 8, 8)

        latest = create_wellness_day()
        latest.date = date(2026, 8, 9)
        latest.sleep_score = 77.0
        latest.hrv = 52.0

        repository.save_wellness_day(
            profile.id,
            older,
        )

        repository.save_wellness_day(
            profile.id,
            latest,
        )

        result = repository.get_latest(
            profile.id,
        )

        assert result is not None
        assert result.date == date(2026, 8, 9)
        assert result.sleep_score == 77.0
        assert result.hrv == 52.0

    finally:
        db.close()

def test_sql_wellness_repository_returns_none_when_empty() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        result = repository.get_latest(
            profile.id,
        )

        assert result is None

    finally:
        db.close()

def test_sql_wellness_repository_lists_range() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        for day_number in range(1, 6):
            wellness = create_wellness_day()
            wellness.date = date(
                2026,
                8,
                day_number,
            )
            wellness.hrv = float(
                40 + day_number
            )

            repository.save_wellness_day(
                profile.id,
                wellness,
            )

        result = repository.list_range(
            profile.id,
            date(2026, 8, 2),
            date(2026, 8, 4),
            provider="intervals",
        )

        assert len(result) == 3

        assert [
            wellness.date
            for wellness in result
        ] == [
            date(2026, 8, 2),
            date(2026, 8, 3),
            date(2026, 8, 4),
        ]

    finally:
        db.close()


def test_sql_wellness_repository_filters_provider() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        intervals = create_wellness_day()
        intervals.date = date(
            2026,
            8,
            10,
        )
        intervals.provider = "intervals"

        suunto = create_wellness_day()
        suunto.date = date(
            2026,
            8,
            10,
        )
        suunto.provider = "suunto"

        repository.save_wellness_day(
            profile.id,
            intervals,
        )

        repository.save_wellness_day(
            profile.id,
            suunto,
        )

        result = repository.list_range(
            profile.id,
            date(2026, 8, 10),
            date(2026, 8, 10),
            provider="intervals",
        )

        assert len(result) == 1
        assert result[0].provider == "intervals"

    finally:
        db.close()

def test_sql_wellness_repository_gets_day_by_date() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        wellness = create_wellness_day()
        wellness.date = date(
            2026,
            8,
            18,
        )
        wellness.hrv = 52.0

        repository.save_wellness_day(
            profile.id,
            wellness,
        )

        result = repository.get_by_date(
            profile.id,
            date(2026, 8, 18),
            provider="intervals",
        )

        assert result is not None
        assert result.date == date(
            2026,
            8,
            18,
        )
        assert result.provider == "intervals"
        assert result.hrv == 52.0

    finally:
        db.close()


def test_sql_wellness_repository_get_by_date_filters_provider() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        intervals = create_wellness_day()
        intervals.date = date(
            2026,
            8,
            18,
        )
        intervals.provider = "intervals"

        suunto = create_wellness_day()
        suunto.date = date(
            2026,
            8,
            18,
        )
        suunto.provider = "suunto"

        repository.save_wellness_day(
            profile.id,
            intervals,
        )

        repository.save_wellness_day(
            profile.id,
            suunto,
        )

        result = repository.get_by_date(
            profile.id,
            date(2026, 8, 18),
            provider="suunto",
        )

        assert result is not None
        assert result.provider == "suunto"

    finally:
        db.close()


def test_sql_wellness_repository_get_by_date_returns_none_when_missing() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        result = repository.get_by_date(
            profile.id,
            date(2026, 8, 18),
            provider="intervals",
        )

        assert result is None

    finally:
        db.close()

def test_sql_wellness_repository_gets_latest_on_or_before() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        for day_number in (
            15,
            17,
            19,
        ):
            wellness = create_wellness_day()
            wellness.date = date(
                2026,
                8,
                day_number,
            )

            repository.save_wellness_day(
                profile.id,
                wellness,
            )

        result = (
            repository
            .get_latest_on_or_before(
                profile.id,
                date(2026, 8, 18),
                provider="intervals",
            )
        )

        assert result is not None
        assert result.date == date(
            2026,
            8,
            17,
        )

    finally:
        db.close()


def test_sql_wellness_repository_latest_on_or_before_filters_provider() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        intervals = create_wellness_day()
        intervals.date = date(
            2026,
            8,
            16,
        )
        intervals.provider = "intervals"

        suunto = create_wellness_day()
        suunto.date = date(
            2026,
            8,
            17,
        )
        suunto.provider = "suunto"

        repository.save_wellness_day(
            profile.id,
            intervals,
        )

        repository.save_wellness_day(
            profile.id,
            suunto,
        )

        result = (
            repository
            .get_latest_on_or_before(
                profile.id,
                date(2026, 8, 18),
                provider="intervals",
            )
        )

        assert result is not None
        assert result.provider == "intervals"
        assert result.date == date(
            2026,
            8,
            16,
        )

    finally:
        db.close()


def test_sql_wellness_repository_latest_on_or_before_returns_none_when_unavailable() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlWellnessRepository(db)

        wellness = create_wellness_day()
        wellness.date = date(
            2026,
            8,
            19,
        )

        repository.save_wellness_day(
            profile.id,
            wellness,
        )

        result = (
            repository
            .get_latest_on_or_before(
                profile.id,
                date(2026, 8, 18),
                provider="intervals",
            )
        )

        assert result is None

    finally:
        db.close()