from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.coaching.constraints import (
    get_athlete_constraint_planning_service,
)
from opencoach.api.intervals import (
    get_current_athlete_profile_id,
)
from opencoach.models import AthleteConstraint


class FakeConstraintPlanningService:
    def __init__(self) -> None:
        self.saved: list[
            dict[str, object]
        ] = []

        self.deleted: list[
            dict[str, object]
        ] = []

    def save(
        self,
        *,
        athlete_profile_id,
        constraint,
        reference_date,
    ):
        self.saved.append(
            {
                "athlete_profile_id": athlete_profile_id,
                "constraint": constraint,
                "reference_date": reference_date,
            }
        )

        return constraint

    def delete(
        self,
        *,
        athlete_profile_id,
        constraint_id,
        reference_date,
    ) -> None:
        self.deleted.append(
            {
                "athlete_profile_id": athlete_profile_id,
                "constraint_id": constraint_id,
                "reference_date": reference_date,
            }
        )


def _client():
    app = create_app()

    athlete_profile_id = uuid4()

    service = (
        FakeConstraintPlanningService()
    )

    app.dependency_overrides[
        get_current_athlete_profile_id
    ] = lambda: athlete_profile_id

    app.dependency_overrides[
        get_athlete_constraint_planning_service
    ] = lambda: service

    return (
        TestClient(app),
        service,
        athlete_profile_id,
    )


def test_create_work_constraint_uses_planning_service() -> None:
    client, service, athlete_profile_id = (
        _client()
    )

    response = client.post(
        "/api/coach/constraints",
        json={
            "start_date": "2026-08-26",
            "end_date": "2026-08-26",
            "constraint_type": "work",
            "availability": "unavailable",
            "running_allowed": False,
            "cross_training_allowed": False,
            "notes": (
                "Absence professionnelle"
            ),
        },
    )

    assert response.status_code == 201

    assert len(
        service.saved
    ) == 1

    call = service.saved[0]

    assert (
        call[
            "athlete_profile_id"
        ]
        == athlete_profile_id
    )

    constraint = call[
        "constraint"
    ]

    assert isinstance(
        constraint,
        AthleteConstraint,
    )

    assert (
        constraint.constraint_type
        == "work"
    )

    assert (
        constraint.availability
        == "unavailable"
    )

    assert (
        constraint.start_date
        == date(
            2026,
            8,
            26,
        )
    )


def test_create_illness_constraint_uses_same_pipeline() -> None:
    client, service, _ = (
        _client()
    )

    response = client.post(
        "/api/coach/constraints",
        json={
            "start_date": "2026-08-25",
            "end_date": "2026-08-27",
            "constraint_type": "illness",
            "availability": "unavailable",
            "running_allowed": False,
            "cross_training_allowed": False,
            "notes": "Malade",
        },
    )

    assert response.status_code == 201

    assert len(
        service.saved
    ) == 1

    constraint = (
        service.saved[0][
            "constraint"
        ]
    )

    assert (
        constraint.constraint_type
        == "illness"
    )


def test_update_constraint_uses_same_id() -> None:
    client, service, _ = (
        _client()
    )

    constraint_id = uuid4()

    response = client.put(
        (
            "/api/coach/constraints/"
            f"{constraint_id}"
        ),
        json={
            "start_date": "2026-08-27",
            "end_date": "2026-08-27",
            "constraint_type": "work",
            "availability": "limited",
            "running_allowed": True,
            "cross_training_allowed": True,
            "max_duration_minutes": 30,
        },
    )

    assert response.status_code == 200

    assert len(
        service.saved
    ) == 1

    constraint = (
        service.saved[0][
            "constraint"
        ]
    )

    assert (
        constraint.id
        == constraint_id
    )

    assert (
        constraint.availability
        == "limited"
    )

    assert (
        constraint.max_duration_minutes
        == 30
    )


def test_delete_constraint_uses_planning_service() -> None:
    client, service, athlete_profile_id = (
        _client()
    )

    constraint_id = uuid4()

    response = client.delete(
        (
            "/api/coach/constraints/"
            f"{constraint_id}"
        )
    )

    assert response.status_code == 204

    assert len(
        service.deleted
    ) == 1

    call = service.deleted[0]

    assert (
        call[
            "athlete_profile_id"
        ]
        == athlete_profile_id
    )

    assert (
        call[
            "constraint_id"
        ]
        == constraint_id
    )


def test_invalid_constraint_dates_are_rejected() -> None:
    client, service, _ = (
        _client()
    )

    response = client.post(
        "/api/coach/constraints",
        json={
            "start_date": "2026-08-28",
            "end_date": "2026-08-26",
            "constraint_type": "work",
            "availability": "unavailable",
        },
    )

    assert response.status_code == 422

    assert (
        service.saved
        == []
    )
