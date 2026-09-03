from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.intervals import (
    get_current_athlete_profile_id,
)
from opencoach.api.training_stats import (
    get_training_stats_service,
)
from opencoach.training import (
    TrainingStats,
)


START_DATE = date(
    2026,
    1,
    1,
)

END_DATE = date(
    2026,
    8,
    21,
)


class FakeTrainingStatsService:
    def __init__(
        self,
        result: TrainingStats,
    ) -> None:
        self.result = result
        self.calls = []

    def calculate(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ) -> TrainingStats:
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return self.result


def create_stats() -> TrainingStats:
    return TrainingStats(
        start_date=START_DATE,
        end_date=END_DATE,
        activities_count=42,
        manual_sessions_count=3,
        total_duration_minutes=3180,
        total_distance_km=512.34,
        total_elevation_gain_m=12850.0,
        measured_load=1450.0,
        estimated_load=95.0,
    )


def create_client(
    service: FakeTrainingStatsService,
):
    app = create_app()

    profile_id = uuid4()

    app.dependency_overrides[
        get_current_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_training_stats_service
    ] = lambda: service

    return (
        TestClient(app),
        profile_id,
    )


def test_training_stats_api_returns_actual_stats() -> None:
    service = FakeTrainingStatsService(
        create_stats()
    )

    client, profile_id = create_client(
        service
    )

    response = client.get(
        "/api/training-stats",
        params={
            "start": START_DATE.isoformat(),
            "end": END_DATE.isoformat(),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["start_date"] == (
        START_DATE.isoformat()
    )

    assert payload["end_date"] == (
        END_DATE.isoformat()
    )

    assert payload["activities_count"] == 42
    assert payload["manual_sessions_count"] == 3
    assert payload["sessions_count"] == 45

    assert payload["total_duration_minutes"] == 3180
    assert payload["total_distance_km"] == 512.34

    assert (
        payload["total_elevation_gain_m"]
        == 12850.0
    )

    assert payload["measured_load"] == 1450.0
    assert payload["estimated_load"] == 95.0
    assert payload["total_load"] == 1545.0

    assert service.calls == [
        (
            profile_id,
            START_DATE,
            END_DATE,
        )
    ]
