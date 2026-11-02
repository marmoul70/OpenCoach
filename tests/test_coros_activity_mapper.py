from datetime import datetime
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
