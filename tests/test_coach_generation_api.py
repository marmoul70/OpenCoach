"""Tests HTTP de la génération hebdomadaire du coach."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import (
    TestClient,
)

from opencoach.api.app import (
    create_app,
)
from opencoach.api.coaching.dependencies import (
    get_generate_planned_training_week_service,
    get_weekly_planning_context_builder,
)
from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.coaching.generation import (
    GenerateAndPersistTrainingWeekResult,
    GeneratePlannedTrainingWeekResult,
)
from opencoach.coaching.generation.models import (
    GeneratedTrainingWeek,
)
from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


ATHLETE_ID = uuid4()


class FakeContextBuilder:
    def build(
        self,
        *,
        athlete_profile_id,
        planning_date,
        trajectory_start_date,
    ):
        assert (
            athlete_profile_id
            == ATHLETE_ID
        )

        return SimpleNamespace(
            planning_input=(
                SimpleNamespace()
            )
        )


class FakeGenerationService:
    def execute(
        self,
        *,
        athlete_profile_id,
        planning_input,
        physiological_reference_date=None,
        additional_context=(),
    ):
        del planning_input

        assert (
            athlete_profile_id
            == ATHLETE_ID
        )

        assert (
            physiological_reference_date
            == date(
                2027,
                7,
                5,
            )
        )

        session = TrainingSession(
            id=uuid4(),
            date=date(
                2027,
                7,
                7,
            ),
            type="threshold",
            sport_type="Run",
            title="Travail au seuil",
            description=(
                "3 × 10 min au seuil."
            ),
            duration_minutes=70,
            planning_key=(
                "2027-07-05:threshold"
            ),
            intensity=(
                "RPE 7–8"
            ),
            heart_rate_zone=(
                "157–165 bpm"
            ),
            status="planned",
        )

        week = GeneratedTrainingWeek(
            week_start=date(
                2027,
                7,
                5,
            ),
            week_end=date(
                2027,
                7,
                11,
            ),
            phase=(
                TrainingPhase.SPECIFIC
            ),
            sessions=(),
            target_load=420.0,
        )

        generation = (
            GenerateAndPersistTrainingWeekResult(
                generated_week=week,
                persisted_sessions=(
                    session,
                ),
            )
        )

        return GeneratePlannedTrainingWeekResult(
            planning=SimpleNamespace(),
            generation=generation,
        )


def create_client() -> TestClient:
    app = create_app()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: ATHLETE_ID

    app.dependency_overrides[
        get_weekly_planning_context_builder
    ] = lambda: FakeContextBuilder()

    app.dependency_overrides[
        get_generate_planned_training_week_service
    ] = lambda: FakeGenerationService()

    return TestClient(
        app
    )


def test_generate_week_returns_persisted_sessions() -> None:
    client = create_client()

    response = client.post(
        (
            "/api/coach/weeks/"
            "2027-07-05/generate"
        ),
        json={},
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["week_start"]
        == "2027-07-05"
    )

    assert (
        payload["week_end"]
        == "2027-07-11"
    )

    assert (
        payload["phase"]
        == "specific"
    )

    assert (
        payload["session_count"]
        == 1
    )

    assert len(
        payload["sessions"]
    ) == 1

    session = payload[
        "sessions"
    ][0]

    assert (
        session["title"]
        == "Travail au seuil"
    )

    assert (
        session["planning_key"]
        == "2027-07-05:threshold"
    )


def test_week_start_must_be_monday() -> None:
    client = create_client()

    response = client.post(
        (
            "/api/coach/weeks/"
            "2027-07-06/generate"
        ),
        json={},
    )

    assert response.status_code == 422


def test_trajectory_start_cannot_be_after_week() -> None:
    client = create_client()

    response = client.post(
        (
            "/api/coach/weeks/"
            "2027-07-05/generate"
        ),
        json={
            "trajectory_start_date":
                "2027-07-12",
        },
    )

    assert response.status_code == 422
