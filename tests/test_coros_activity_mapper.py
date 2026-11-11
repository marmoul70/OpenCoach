from datetime import datetime, timezone
from uuid import uuid4

from opencoach.integrations.coros.activity_mapper import upsert_coros_activity


class FakeDb:
    def __init__(self):
        self.added = []

    def scalar(self, statement):
        return None

    def add(self, row):
        self.added.append(row)


def test_coros_activity_maps_to_canonical_activity_model():
    db = FakeDb()
    profile_id = uuid4()
    saved = upsert_coros_activity(db, profile_id, {
        "labelId": "activity-42",
        "sportType": 102,
        "startTimestamp": 1790000000,
        "workoutTime": 5400,
    })

    assert saved is True
    assert len(db.added) == 1
    activity = db.added[0]
    assert activity.athlete_profile_id == profile_id
    assert activity.provider == "coros"
    assert activity.provider_activity_id == "activity-42"
    assert activity.sport_type == "Trail"
    assert activity.elapsed_time_seconds == 5400
    assert isinstance(activity.start_at, datetime)


def test_coros_activity_without_stable_id_or_timestamp_is_skipped():
    db = FakeDb()
    assert upsert_coros_activity(db, uuid4(), {"sportType": 102}) is False
    assert db.added == []


def test_coros_activity_maps_available_metrics_and_string_sport_name():
    db = FakeDb()
    profile_id = uuid4()
    assert upsert_coros_activity(db, profile_id, {
        "labelId": "activity-metrics",
        "sportType": "Trail Running",
        "startTimestamp": 1790000000000,
        "workoutTime": 3600,
        "distanceMeters": 12500,
        "totalAscent": 650,
        "avgHr": 148,
        "maxHr": 176,
        "average_speed_mps": 3.2,
        "calories": 850,
    }) is True

    activity = db.added[0]
    assert activity.sport_type == "Trail Running"
    assert activity.elapsed_time_seconds == 3600
    assert activity.distance_m == 12500
    assert activity.elevation_gain_m == 650
    assert activity.average_heart_rate == 148
    assert activity.max_heart_rate == 176
    assert activity.average_speed_mps == 3.2
    assert activity.calories == 850


def test_coros_activity_keeps_unknown_sport_code_instead_of_guessing():
    db = FakeDb()
    assert upsert_coros_activity(db, uuid4(), {
        "labelId": "unknown-sport",
        "sportType": 987654,
        "startTimestamp": 1790000000,
    }) is True
    assert db.added[0].sport_type == "COROS (987654)"


def test_sparse_coros_update_preserves_existing_metrics():
    from types import SimpleNamespace

    profile_id = uuid4()
    existing = SimpleNamespace(
        athlete_profile_id=profile_id,
        name="Trail",
        sport_type="Trail",
        start_at=datetime.fromtimestamp(1790000000),
        elapsed_time_seconds=5400,
        distance_m=12500.0,
        elevation_gain_m=650.0,
        average_heart_rate=148.0,
        max_heart_rate=176.0,
    )

    class ExistingDb(FakeDb):
        def scalar(self, statement):
            return existing

    db = ExistingDb()
    assert upsert_coros_activity(db, profile_id, {
        "labelId": "activity-42",
        "sportType": 102,
        "startTimestamp": 1790000000,
    }) is True

    assert db.added == []
    assert existing.elapsed_time_seconds == 5400
    assert existing.distance_m == 12500.0
    assert existing.elevation_gain_m == 650.0
    assert existing.average_heart_rate == 148.0
    assert existing.max_heart_rate == 176.0



def test_coros_activity_from_another_profile_is_not_modified():
    from types import SimpleNamespace

    existing_profile_id = uuid4()
    importing_profile_id = uuid4()
    existing = SimpleNamespace(
        athlete_profile_id=existing_profile_id,
        name="Existing profile run",
        sport_type="Trail",
        start_at=datetime.fromtimestamp(1790000000),
        elapsed_time_seconds=5400,
        distance_m=12500.0,
    )

    class ExistingDb(FakeDb):
        def scalar(self, statement):
            return existing

    db = ExistingDb()
    saved = upsert_coros_activity(db, importing_profile_id, {
        "labelId": "activity-42",
        "sportType": 102,
        "startTimestamp": 1790000000,
        "workoutTime": 3600,
    })

    assert saved is False
    assert db.added == []
    assert existing.athlete_profile_id == existing_profile_id
    assert existing.name == "Existing profile run"
    assert existing.elapsed_time_seconds == 5400
    assert existing.distance_m == 12500.0


def test_coros_activity_maps_utc_timestamp_to_paris_local_date():
    db = FakeDb()
    profile_id = uuid4()
    timestamp = datetime(
        2026, 11, 10, 8, 15, tzinfo=timezone.utc
    ).timestamp()

    saved = upsert_coros_activity(db, profile_id, {
        "labelId": "activity-local-date",
        "sportType": 100,
        "startTimestamp": timestamp,
        "workoutTime": 3600,
    })

    assert saved is True
    activity = db.added[0]
    assert activity.start_at == datetime(2026, 11, 10, 8, 15)
    assert activity.start_at_local == datetime(2026, 11, 10, 9, 15)
    assert activity.moving_time_seconds == 3600
    assert activity.elapsed_time_seconds == 3600


def test_coros_activity_updates_local_timestamp_on_existing_record():
    from types import SimpleNamespace

    profile_id = uuid4()
    existing = SimpleNamespace(
        athlete_profile_id=profile_id,
        name="Course",
        sport_type="Course extérieure",
        start_at=datetime(2026, 11, 10, 8, 15),
        start_at_local=None,
        elapsed_time_seconds=None,
        moving_time_seconds=None,
        distance_m=None,
        elevation_gain_m=None,
        average_heart_rate=None,
        max_heart_rate=None,
        average_speed_mps=None,
        calories=None,
    )

    class ExistingDb(FakeDb):
        def scalar(self, statement):
            return existing

    timestamp = datetime(
        2026, 11, 10, 8, 15, tzinfo=timezone.utc
    ).timestamp()
    assert upsert_coros_activity(ExistingDb(), profile_id, {
        "labelId": "activity-existing",
        "sportType": 100,
        "startTimestamp": timestamp,
    }) is True

    assert existing.start_at_local == datetime(2026, 11, 10, 9, 15)
