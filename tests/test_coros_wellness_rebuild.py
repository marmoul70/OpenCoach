from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    CorosDailyData,
    User,
    WellnessDaily,
)
from opencoach.database.repositories import SqlWellnessRepository
from opencoach.integrations.coros.sync import rebuild_wellness_from_snapshots
from opencoach.models import WellnessDay


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return session_factory()


def create_profile(db):
    user = User(email="rebuild-test@opencoach.local")
    profile = AthleteProfile(
        user=user,
        first_name="Test",
        last_name="Rebuild",
    )
    db.add(profile)
    db.commit()
    return profile


def add_snapshot(db, profile_id, category, metric_date, report):
    db.add(
        CorosDailyData(
            athlete_profile_id=profile_id,
            metric_date=metric_date,
            category=category,
            payload={"data": report},
        )
    )
    db.commit()


def test_rebuild_dry_run_reports_creations_without_writing() -> None:
    db = create_session()
    try:
        profile = create_profile(db)
        add_snapshot(
            db,
            profile.id,
            "sleep",
            date(2026, 9, 26),
            """Sleep Overview
2026-10-01
Sleep Score: 82
Main Sleep (asleep): 7h 30min
""",
        )

        result = rebuild_wellness_from_snapshots(
            db,
            profile.id,
            date(2026, 10, 1),
            date(2026, 10, 1),
        )

        assert result == {
            "snapshots_scanned": 1,
            "mapped_days": 1,
            "created": 1,
            "updated": 0,
            "skipped": 0,
            "dry_run": True,
        }
        assert db.scalars(select(WellnessDaily)).all() == []
    finally:
        db.close()


def test_rebuild_merges_categories_preserves_existing_values_and_intervals() -> None:
    db = create_session()
    try:
        profile = create_profile(db)
        repository = SqlWellnessRepository(db)

        repository.save_wellness_day(
            profile.id,
            WellnessDay(
                provider="intervals",
                date=date(2026, 11, 2),
                hrv=99,
                sleep_score=75,
            ),
        )
        repository.save_wellness_day(
            profile.id,
            WellnessDay(
                provider="coros",
                date=date(2026, 11, 2),
                hrv=45,
            ),
        )

        add_snapshot(
            db,
            profile.id,
            "sleep",
            date(2026, 11, 2),
            """Sleep Overview
2026-11-02
Sleep Score: 90
Main Sleep (asleep): 7h 30min
""",
        )
        add_snapshot(
            db,
            profile.id,
            "hrv",
            date(2026, 11, 2),
            """Sleep HRV — Last 1 day
2026-11-02:
  HRV Avg: 50 ms
  Baseline: 42 ms
""",
        )
        add_snapshot(
            db,
            profile.id,
            "heart_rate",
            date(2026, 11, 2),
            """Average Heart Rate — Last 1 day
2026-11-02: 60 bpm (Min: 42, Max: 130)
""",
        )

        result = rebuild_wellness_from_snapshots(
            db,
            profile.id,
            date(2026, 11, 2),
            date(2026, 11, 2),
            dry_run=False,
        )

        assert result["created"] == 0
        assert result["updated"] == 1
        assert result["skipped"] == 0

        rows = db.scalars(
            select(WellnessDaily).where(
                WellnessDaily.athlete_profile_id == profile.id,
                WellnessDaily.date == date(2026, 11, 2),
            )
        ).all()
        by_provider = {row.provider: row for row in rows}

        assert set(by_provider) == {"coros", "intervals"}
        assert by_provider["coros"].hrv == 45
        assert by_provider["coros"].hrv_baseline == 42
        assert by_provider["coros"].sleep_score == 90
        assert by_provider["coros"].sleep_seconds == 27_000
        assert by_provider["coros"].avg_hr == 60
        assert by_provider["coros"].min_hr == 42
        assert by_provider["coros"].max_hr == 130
        assert by_provider["intervals"].hrv == 99
        assert by_provider["intervals"].sleep_score == 75

        second_run = rebuild_wellness_from_snapshots(
            db,
            profile.id,
            date(2026, 11, 2),
            date(2026, 11, 2),
            dry_run=False,
        )
        assert second_run["created"] == 0
        assert second_run["updated"] == 0
        assert second_run["skipped"] == 1
    finally:
        db.close()


def test_rebuild_creates_one_day_from_multiday_report_and_respects_date_range() -> None:
    db = create_session()
    try:
        profile = create_profile(db)
        add_snapshot(
            db,
            profile.id,
            "sleep",
            date(2026, 9, 26),
            """Sleep Overview
2026-10-01
Sleep Score: 0
Sleep detail for this day is not available yet.

2026-10-02
Sleep Score: 78
Daily Sleep: 7h 59min (incl. naps)
Main Sleep (asleep): 7h 59min
""",
        )

        result = rebuild_wellness_from_snapshots(
            db,
            profile.id,
            date(2026, 10, 1),
            date(2026, 10, 2),
            dry_run=False,
        )

        assert result["mapped_days"] == 1
        assert result["created"] == 1
        rows = db.scalars(select(WellnessDaily)).all()
        assert len(rows) == 1
        assert rows[0].date == date(2026, 10, 2)
        assert rows[0].sleep_score == 78
    finally:
        db.close()


def test_rebuild_rejects_invalid_date_range() -> None:
    db = create_session()
    try:
        profile = create_profile(db)
        with pytest.raises(ValueError, match="start_date"):
            rebuild_wellness_from_snapshots(
                db,
                profile.id,
                date(2026, 11, 3),
                date(2026, 11, 2),
            )
    finally:
        db.close()


def test_rebuild_skips_metadata_only_snapshots() -> None:
    db = create_session()
    try:
        profile = create_profile(db)
        db.add(
            CorosDailyData(
                athlete_profile_id=profile.id,
                metric_date=date(2026, 11, 2),
                category="sleep",
                payload={"updatedAt": "2026-11-02T08:00:00Z"},
            )
        )
        db.commit()

        result = rebuild_wellness_from_snapshots(
            db,
            profile.id,
            date(2026, 11, 2),
            date(2026, 11, 2),
            dry_run=False,
        )

        assert result["snapshots_scanned"] == 1
        assert result["mapped_days"] == 0
        assert result["created"] == 0
        assert result["updated"] == 0
        assert db.scalars(select(WellnessDaily)).all() == []
    finally:
        db.close()

