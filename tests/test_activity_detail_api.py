from datetime import date, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.authentication.dependencies import get_current_athlete_profile_id
from opencoach.database.session import get_db


class FakeScalarResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeDatabase:
    def __init__(self, activity, snapshots):
        self.activity = activity
        self.snapshots = snapshots

    def scalar(self, statement):
        return self.activity

    def scalars(self, statement):
        return FakeScalarResult(self.snapshots)


def make_client(activity, snapshots, profile_id):
    db = FakeDatabase(activity, snapshots)
    app = create_app()
    app.dependency_overrides[get_current_athlete_profile_id] = lambda: profile_id
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_coros_activity_detail_returns_saved_snapshot():
    profile_id = uuid4()
    activity_id = uuid4()
    activity = SimpleNamespace(
        id=activity_id,
        athlete_profile_id=profile_id,
        provider="coros",
        provider_activity_id="481446507948572982",
        name="Lyoffans Trail",
        sport_type="Trail",
        start_at=datetime(2026, 11, 1, 8, 7),
        start_at_local=None,
        distance_m=18750.0,
        elapsed_time_seconds=7090,
        moving_time_seconds=None,
        elevation_gain_m=None,
        elevation_loss_m=None,
        average_heart_rate=140.0,
        max_heart_rate=None,
        average_speed_mps=None,
        average_power_w=None,
        average_cadence=None,
        average_stride_m=None,
        calories=1311,
        training_load=None,
    )
    raw_detail = {"text": "Average Pace: 6:18 /km\\nElevation Gain / Loss: 424 m / 431 m"}
    snapshot = SimpleNamespace(
        metric_date=date(2026, 11, 1),
        payload={
            "activities": [{
                "labelId": "481446507948572982",
                "activity_detail": raw_detail,
            }]
        },
    )

    client = make_client(activity, [snapshot], profile_id)
    response = client.get("/api/activities/provider/coros/481446507948572982/detail")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Lyoffans Trail"
    assert payload["coros_detail"] == raw_detail
    assert payload["coros_record"]["labelId"] == "481446507948572982"


def test_activity_detail_does_not_return_another_profile_activity():
    profile_id = uuid4()
    activity_id = uuid4()
    client = make_client(None, [], profile_id)

    response = client.get(f"/api/activities/{activity_id}/detail")

    assert response.status_code == 404
