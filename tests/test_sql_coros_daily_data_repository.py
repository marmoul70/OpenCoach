from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    CorosDailyData,
    User,
)
from opencoach.database.repositories.sql_coros_daily_data import (
    SqlCorosDailyDataRepository,
)


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def create_profile(db):
    user = User(email="series@opencoach.local")
    profile = AthleteProfile(
        user=user,
        first_name="Test",
        last_name="Athlete",
    )
    db.add(profile)
    db.commit()
    return profile


def test_repository_lists_only_normalized_time_series_in_date_range():
    db = create_session()
    try:
        profile = create_profile(db)
        other_profile = create_profile(db)
        db.add_all([
            CorosDailyData(
                athlete_profile_id=profile.id,
                metric_date=date(2026, 11, 1),
                category="hrv_timeseries",
                payload={"samples": [{"metric": "sleep_hrv", "value": 48}]},
            ),
            CorosDailyData(
                athlete_profile_id=profile.id,
                metric_date=date(2026, 11, 2),
                category="stress_points",
                payload={"samples": [{"metric": "stress", "value": 31}]},
            ),
            CorosDailyData(
                athlete_profile_id=profile.id,
                metric_date=date(2026, 11, 2),
                category="sleep",
                payload={"sleepScore": 90},
            ),
            CorosDailyData(
                athlete_profile_id=profile.id,
                metric_date=date(2026, 10, 31),
                category="health_check_points",
                payload={"samples": []},
            ),
            CorosDailyData(
                athlete_profile_id=other_profile.id,
                metric_date=date(2026, 11, 2),
                category="hrv_timeseries",
                payload={"samples": [{"metric": "sleep_hrv", "value": 99}]},
            ),
        ])
        db.commit()

        result = SqlCorosDailyDataRepository(db).list_time_series_snapshots(
            profile.id,
            date(2026, 11, 1),
            date(2026, 11, 2),
        )

        assert [item["category"] for item in result] == [
            "hrv_timeseries",
            "stress_points",
        ]
        assert result[0]["payload"]["samples"][0]["value"] == 48
    finally:
        db.close()
