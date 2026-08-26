from datetime import date
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.coaching.dependencies import (
    get_daily_adaptation_repository,
    get_daily_checkin_repository,
    get_training_session_repository,
)
from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)
from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
)
from opencoach.models import (
    TrainingSession,
)


class FakeDailyCheckInRepository:
    def __init__(self) -> None:
        self.checkin = None

    def save(
        self,
        athlete_profile_id,
        checkin,
    ):
        del athlete_profile_id

        saved = AthleteDailyCheckIn(
            id=(
                self.checkin.id
                if self.checkin is not None
                else uuid4()
            ),
            date=checkin.date,
            energy_rating=checkin.energy_rating,
            pain_wellness_rating=(
                checkin.pain_wellness_rating
            ),
            illness=checkin.illness,
            unavailable=checkin.unavailable,
            pain_locations=checkin.pain_locations,
            note=checkin.note,
        )

        self.checkin = saved

        return saved

    def get_for_date(
        self,
        athlete_profile_id,
        checkin_date,
    ):
        del athlete_profile_id

        if self.checkin is None:
            return None

        if self.checkin.date != checkin_date:
            return None

        return self.checkin


class FakeDailyAdaptationRepository:
    def __init__(self) -> None:
        self.proposals = {}

    def save(
        self,
        athlete_profile_id,
        proposal,
    ):
        del athlete_profile_id

        saved = CoachAdaptationProposal(
            id=(
                proposal.id
                if proposal.id is not None
                else uuid4()
            ),
            checkin_id=proposal.checkin_id,
            reason=proposal.reason,
            recommendation=(
                proposal.recommendation
            ),
            decision=proposal.decision,
        )

        self.proposals[
            saved.checkin_id
        ] = saved

        return saved

    def delete_for_checkin(
        self,
        athlete_profile_id,
        checkin_id,
    ):
        del athlete_profile_id

        self.proposals.pop(
            checkin_id,
            None,
        )

    def get_for_checkin(
        self,
        athlete_profile_id,
        checkin_id,
    ):
        del athlete_profile_id

        return self.proposals.get(
            checkin_id
        )



class FakeTrainingSessionRepository:
    def __init__(self) -> None:
        self.sessions = [
            TrainingSession(
                id=uuid4(),
                date=date.today(),
                type="threshold",
                sport_type="Run",
                title="Travail au seuil",
                description="Séance qualitative.",
                duration_minutes=60,
                intensity="hard",
                status="planned",
                planning_key=(
                    f"{date.today().isoformat()}:threshold"
                ),
            )
        ]

        self.saved = []

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        del athlete_profile_id

        return [
            session
            for session in self.sessions
            if (
                start_date
                <= session.date
                <= end_date
            )
        ]

    def save_session(
        self,
        athlete_profile_id,
        session,
    ):
        del athlete_profile_id

        self.saved.append(
            session
        )

        for index, existing in enumerate(
            self.sessions
        ):
            if existing.id == session.id:
                self.sessions[index] = session
                break

        return session

def _client():
    app = create_app()

    athlete_profile_id = uuid4()

    checkins = (
        FakeDailyCheckInRepository()
    )

    adaptations = (
        FakeDailyAdaptationRepository()
    )

    training_sessions = (
        FakeTrainingSessionRepository()
    )

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: athlete_profile_id

    app.dependency_overrides[
        get_daily_checkin_repository
    ] = lambda: checkins

    app.dependency_overrides[
        get_daily_adaptation_repository
    ] = lambda: adaptations

    app.dependency_overrides[
        get_training_session_repository
    ] = lambda: training_sessions

    return (
        TestClient(app),
        checkins,
        adaptations,
        training_sessions,
    )


def test_good_checkin_creates_no_adaptation() -> None:
    client, _, _, _ = _client()

    response = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 5,
            "illness": False,
            "unavailable": False,
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert (
        payload["checkin"][
            "energy_rating"
        ]
        == 5
    )

    assert payload["adaptation"] is None


def test_three_hearts_creates_pending_proposal() -> None:
    client, _, _, _ = _client()

    response = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 3,
            "pain_locations": [
                {
                    "area": "lower_back",
                    "side": "center",
                }
            ],
        },
    )

    assert response.status_code == 201

    adaptation = (
        response.json()[
            "adaptation"
        ]
    )

    assert adaptation is not None

    assert (
        adaptation["decision"]
        == "pending"
    )

    assert (
        adaptation[
            "awaiting_athlete_decision"
        ]
        is True
    )

    assert (
        adaptation[
            "adaptation_authorized"
        ]
        is False
    )

    assert (
        "lower_back:center"
        in adaptation["reason"]
    )


def test_three_stars_creates_pending_proposal() -> None:
    client, _, _, _ = _client()

    response = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 3,
            "pain_wellness_rating": 5,
        },
    )

    assert response.status_code == 201

    assert (
        response.json()[
            "adaptation"
        ]["decision"]
        == "pending"
    )


def test_illness_creates_strong_recommendation() -> None:
    client, _, _, _ = _client()

    response = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 5,
            "illness": True,
        },
    )

    assert response.status_code == 201

    adaptation = (
        response.json()[
            "adaptation"
        ]
    )

    assert adaptation is not None

    assert (
        "fortement recommandée"
        in adaptation[
            "recommendation"
        ]
    )


def test_today_returns_saved_checkin_and_proposal() -> None:
    client, _, _, _ = _client()

    created = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 4,
            "pain_wellness_rating": 3,
        },
    )

    assert created.status_code == 201

    response = client.get(
        "/api/coach/check-in/today"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["checkin"]["id"]
        == created.json()[
            "checkin"
        ]["id"]
    )

    assert (
        payload["adaptation"][
            "decision"
        ]
        == "pending"
    )


def test_today_returns_404_without_checkin() -> None:
    client, _, _, _ = _client()

    response = client.get(
        "/api/coach/check-in/today"
    )

    assert response.status_code == 404


def test_athlete_can_accept_proposal() -> None:
    client, _, _, _ = _client()

    created = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 3,
        },
    )

    checkin_id = (
        created.json()[
            "checkin"
        ]["id"]
    )

    response = client.post(
        (
            "/api/coach/check-in/"
            f"{checkin_id}"
            "/adaptation/accept"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["proposal"]["decision"]
        == "accepted"
    )

    assert (
        payload["proposal"][
            "adaptation_authorized"
        ]
        is True
    )

    assert (
        payload["session_adapted"]
        is True
    )

    assert (
        payload["already_accepted"]
        is False
    )

    assert (
        payload["adapted_session"][
            "type"
        ]
        == "aerobic_easy"
    )

    assert (
        payload["adapted_session"][
            "intensity"
        ]
        == "easy"
    )


def test_athlete_can_decline_proposal() -> None:
    client, _, _, _ = _client()

    created = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 3,
            "pain_wellness_rating": 5,
        },
    )

    checkin_id = (
        created.json()[
            "checkin"
        ]["id"]
    )

    response = client.post(
        (
            "/api/coach/check-in/"
            f"{checkin_id}"
            "/adaptation/decline"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["decision"]
        == "declined"
    )

    assert (
        payload[
            "adaptation_authorized"
        ]
        is False
    )


def test_accept_without_proposal_returns_404() -> None:
    client, _, _, _ = _client()

    response = client.post(
        (
            "/api/coach/check-in/"
            f"{uuid4()}"
            "/adaptation/accept"
        )
    )

    assert response.status_code == 404


def test_invalid_rating_is_rejected() -> None:
    client, _, _, _ = _client()

    response = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 6,
            "pain_wellness_rating": 5,
        },
    )

    assert response.status_code == 422


def test_five_hearts_with_location_is_rejected() -> None:
    client, _, _, _ = _client()

    response = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 5,
            "pain_locations": [
                {
                    "area": "knee",
                    "side": "left",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_accept_is_idempotent() -> None:
    client, _, _, training_sessions = (
        _client()
    )

    created = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 3,
        },
    )

    checkin_id = (
        created.json()[
            "checkin"
        ]["id"]
    )

    first = client.post(
        (
            "/api/coach/check-in/"
            f"{checkin_id}"
            "/adaptation/accept"
        )
    )

    assert first.status_code == 200

    assert len(
        training_sessions.saved
    ) == 1

    adapted_duration = (
        training_sessions.sessions[0]
        .duration_minutes
    )

    second = client.post(
        (
            "/api/coach/check-in/"
            f"{checkin_id}"
            "/adaptation/accept"
        )
    )

    assert second.status_code == 200

    payload = second.json()

    assert (
        payload["already_accepted"]
        is True
    )

    assert (
        payload["session_adapted"]
        is False
    )

    assert len(
        training_sessions.saved
    ) == 1

    assert (
        training_sessions.sessions[0]
        .duration_minutes
        == adapted_duration
    )


def test_accept_without_planned_session_returns_409() -> None:
    client, _, _, training_sessions = (
        _client()
    )

    training_sessions.sessions = []

    created = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 3,
        },
    )

    checkin_id = (
        created.json()[
            "checkin"
        ]["id"]
    )

    response = client.post(
        (
            "/api/coach/check-in/"
            f"{checkin_id}"
            "/adaptation/accept"
        )
    )

    assert response.status_code == 409

    assert (
        "Aucune séance planifiée"
        in response.json()["detail"]
    )


def test_accept_with_multiple_sessions_returns_409() -> None:
    client, _, _, training_sessions = (
        _client()
    )

    first = training_sessions.sessions[0]

    second = TrainingSession(
        id=uuid4(),
        date=first.date,
        type="strength",
        sport_type="Strength",
        title="Renforcement",
        description="Séance de renforcement.",
        duration_minutes=30,
        intensity="moderate",
        status="planned",
        planning_key=(
            f"{date.today().isoformat()}:strength"
        ),
    )

    training_sessions.sessions.append(
        second
    )

    created = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 3,
        },
    )

    checkin_id = (
        created.json()[
            "checkin"
        ]["id"]
    )

    response = client.post(
        (
            "/api/coach/check-in/"
            f"{checkin_id}"
            "/adaptation/accept"
        )
    )

    assert response.status_code == 409

    assert (
        "Plusieurs séances"
        in response.json()["detail"]
    )

    assert training_sessions.saved == []


def test_declined_proposal_cannot_later_be_accepted() -> None:
    client, _, _, training_sessions = (
        _client()
    )

    created = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 3,
            "pain_wellness_rating": 5,
        },
    )

    checkin_id = (
        created.json()[
            "checkin"
        ]["id"]
    )

    declined = client.post(
        (
            "/api/coach/check-in/"
            f"{checkin_id}"
            "/adaptation/decline"
        )
    )

    assert declined.status_code == 200

    response = client.post(
        (
            "/api/coach/check-in/"
            f"{checkin_id}"
            "/adaptation/accept"
        )
    )

    assert response.status_code == 409

    assert (
        "déjà été refusée"
        in response.json()["detail"]
    )

    assert training_sessions.saved == []

def test_pending_adaptation_is_removed_when_checkin_returns_to_normal() -> None:
    client, _, adaptations, _ = (
        _client()
    )

    first = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 5,
            "unavailable": True,
        },
    )

    assert first.status_code == 201

    first_payload = first.json()

    assert (
        first_payload["checkin"]["unavailable"]
        is True
    )

    assert (
        first_payload["adaptation"]
        is not None
    )

    assert (
        first_payload["adaptation"]["decision"]
        == "pending"
    )

    checkin_id = first_payload[
        "checkin"
    ]["id"]

    assert len(
        adaptations.proposals
    ) == 1

    second = client.post(
        "/api/coach/check-in",
        json={
            "energy_rating": 5,
            "pain_wellness_rating": 5,
            "illness": False,
            "unavailable": False,
        },
    )

    assert second.status_code == 201

    payload = second.json()

    assert (
        payload["checkin"]["id"]
        == checkin_id
    )

    assert (
        payload["checkin"]["unavailable"]
        is False
    )

    assert (
        payload["checkin"]["illness"]
        is False
    )

    assert (
        payload["checkin"]["energy_rating"]
        == 5
    )

    assert (
        payload["checkin"]["pain_wellness_rating"]
        == 5
    )

    assert (
        payload["adaptation"]
        is None
    )

    assert (
        adaptations.proposals
        == {}
    )

    today = client.get(
        "/api/coach/check-in/today"
    )

    assert today.status_code == 200

    today_payload = today.json()

    assert (
        today_payload["checkin"]["unavailable"]
        is False
    )

    assert (
        today_payload["adaptation"]
        is None
    )
