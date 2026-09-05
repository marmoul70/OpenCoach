from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from opencoach.models import TrainingSession
from opencoach.services.integration_connection import (
    IntegrationCredentials,
)
from opencoach.services.intervals_workout_sync import (
    IntervalsWorkoutSyncService,
    WorkoutSyncStatus,
)


SYNCED_AT = datetime(
    2026,
    9,
    6,
    18,
    3,
    tzinfo=timezone.utc,
)


def make_session(
    *,
    session_id: UUID | None = None,
    duration_minutes: int = 45,
    sport_type: str = "Run",
    status: str = "planned",
) -> TrainingSession:
    return TrainingSession(
        id=session_id or uuid4(),
        date=date(2026, 9, 7),
        type="aerobic_easy",
        sport_type=sport_type,
        title="Endurance facile",
        description="Séance test.",
        duration_minutes=duration_minutes,
        intensity="easy",
        heart_rate_zone=(
            "Fréquence cardiaque individualisée: "
            "129–152 bpm"
        ),
        status=status,
    )


class FakeRepository:
    def __init__(
        self,
        sessions,
    ):
        self.sessions = list(sessions)
        self.list_calls = []
        self.saved = []

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.list_calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return self.sessions

    def save_session(
        self,
        athlete_profile_id,
        session,
    ):
        self.saved.append(
            (
                athlete_profile_id,
                session,
                session.intervals_sync_status,
            )
        )

        return session


class FakeConnectionService:
    def __init__(self):
        self.calls = []

    def get_credentials(
        self,
        athlete_profile_id,
        provider,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                provider,
            )
        )

        return IntegrationCredentials(
            provider="intervals",
            athlete_id="i123456",
            secret="secret-key",
        )


class FakeClient:
    def __init__(
        self,
        *,
        response=None,
        error=None,
    ):
        self.response = response
        self.error = error
        self.calls = []
        self.delete_calls = []

    def upsert_workouts(
        self,
        workouts,
    ):
        self.calls.append(workouts)

        if self.error is not None:
            raise self.error

        if self.response is not None:
            return self.response

        return [
            {
                "id": index + 1000,
                "external_id": workout[
                    "external_id"
                ],
            }
            for index, workout in enumerate(
                workouts
            )
        ]

    def delete_workouts(
        self,
        external_ids,
    ):
        self.delete_calls.append(
            external_ids
        )

        if self.error is not None:
            raise self.error

        return len(external_ids)


def create_service(
    sessions,
    *,
    client=None,
):
    repository = FakeRepository(
        sessions
    )

    connections = FakeConnectionService()

    client = client or FakeClient()

    factory_calls = []

    def factory(
        api_key,
        athlete_id,
    ):
        factory_calls.append(
            (
                api_key,
                athlete_id,
            )
        )

        return client

    service = IntervalsWorkoutSyncService(
        repository=repository,
        connection_service=connections,
        client_factory=factory,
        now=lambda: SYNCED_AT,
    )

    return (
        service,
        repository,
        connections,
        client,
        factory_calls,
    )


def test_new_session_is_synced_and_persisted():
    profile_id = uuid4()
    session = make_session()

    (
        service,
        repository,
        connections,
        client,
        factory_calls,
    ) = create_service([session])

    result = service.sync_period(
        athlete_profile_id=profile_id,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.synced == 1
    assert result.skipped == 0
    assert result.failed == 0

    assert connections.calls == [
        (
            profile_id,
            "intervals",
        )
    ]

    assert factory_calls == [
        (
            "secret-key",
            "i123456",
        )
    ]

    assert len(client.calls) == 1
    assert len(client.calls[0]) == 1

    assert (
        session.intervals_external_id
        == f"opencoach:session:{session.id}"
    )

    assert session.intervals_event_id == "1000"
    assert session.intervals_sync_status == "synced"
    assert (
        session.intervals_last_synced_at
        == SYNCED_AT
    )
    assert session.intervals_payload_hash
    assert session.intervals_sync_error is None

    saved_statuses = [
        status
        for _, _, status in repository.saved
    ]

    assert saved_statuses == [
        "pending",
        "synced",
    ]


def test_same_hash_is_not_sent_again():
    session = make_session()

    (
        first_service,
        _,
        _,
        _,
        _,
    ) = create_service([session])

    first_service.sync_period(
        athlete_profile_id=uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    (
        service,
        repository,
        connections,
        client,
        factory_calls,
    ) = create_service([session])

    result = service.sync_period(
        athlete_profile_id=uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.synced == 0
    assert result.skipped == 1
    assert result.failed == 0

    assert client.calls == []
    assert connections.calls == []
    assert factory_calls == []
    assert repository.saved == []


def test_changed_payload_is_upserted_again():
    profile_id = uuid4()
    session = make_session()

    (
        first_service,
        _,
        _,
        _,
        _,
    ) = create_service([session])

    first_service.sync_period(
        athlete_profile_id=profile_id,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    old_hash = (
        session.intervals_payload_hash
    )

    session.duration_minutes = 60

    (
        service,
        _,
        _,
        client,
        _,
    ) = create_service([session])

    result = service.sync_period(
        athlete_profile_id=profile_id,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.synced == 1
    assert len(client.calls) == 1

    assert (
        session.intervals_payload_hash
        != old_hash
    )

    assert (
        session.intervals_external_id
        == f"opencoach:session:{session.id}"
    )


def test_multiple_sessions_use_one_bulk_call():
    first = make_session()
    second = make_session()

    (
        service,
        _,
        _,
        client,
        _,
    ) = create_service(
        [
            first,
            second,
        ]
    )

    result = service.sync_period(
        athlete_profile_id=uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.synced == 2

    assert len(client.calls) == 1
    assert len(client.calls[0]) == 2


def test_strength_session_is_skipped():
    session = make_session(
        sport_type="Strength",
    )

    (
        service,
        repository,
        connections,
        client,
        _,
    ) = create_service([session])

    result = service.sync_period(
        athlete_profile_id=uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.skipped == 1
    assert result.synced == 0

    assert repository.saved == []
    assert connections.calls == []
    assert client.calls == []


def test_completed_session_is_skipped():
    session = make_session(
        status="completed",
    )

    (
        service,
        repository,
        connections,
        client,
        _,
    ) = create_service([session])

    result = service.sync_period(
        athlete_profile_id=uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.skipped == 1
    assert repository.saved == []
    assert connections.calls == []
    assert client.calls == []


def test_api_failure_marks_all_candidates_failed():
    first = make_session()
    second = make_session()

    client = FakeClient(
        error=RuntimeError(
            "Intervals indisponible"
        )
    )

    (
        service,
        repository,
        _,
        _,
        _,
    ) = create_service(
        [
            first,
            second,
        ],
        client=client,
    )

    result = service.sync_period(
        athlete_profile_id=uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.failed == 2
    assert result.synced == 0

    assert (
        first.intervals_sync_status
        == "failed"
    )
    assert (
        second.intervals_sync_status
        == "failed"
    )

    assert (
        first.intervals_sync_error
        == "Intervals indisponible"
    )

    assert [
        status
        for _, _, status
        in repository.saved
    ] == [
        "pending",
        "pending",
        "failed",
        "failed",
    ]


def test_missing_event_in_bulk_response_is_failed():
    session = make_session()

    client = FakeClient(
        response=[]
    )

    (
        service,
        _,
        _,
        _,
        _,
    ) = create_service(
        [session],
        client=client,
    )

    result = service.sync_period(
        athlete_profile_id=uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.failed == 1
    assert (
        result.items[0].status
        is WorkoutSyncStatus.FAILED
    )

    assert (
        session.intervals_sync_status
        == "failed"
    )


def test_profile_id_is_used_for_read_credentials_and_write():
    profile_id = uuid4()
    session = make_session()

    (
        service,
        repository,
        connections,
        _,
        _,
    ) = create_service([session])

    service.sync_period(
        athlete_profile_id=profile_id,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert repository.list_calls == [
        (
            profile_id,
            date(2026, 9, 7),
            date(2026, 9, 13),
        )
    ]

    assert connections.calls == [
        (
            profile_id,
            "intervals",
        )
    ]

    assert all(
        saved_profile_id == profile_id
        for (
            saved_profile_id,
            _,
            _,
        ) in repository.saved
    )


def test_synced_non_planned_session_is_deleted():
    profile_id = uuid4()

    session = make_session(
        status="skipped",
    )

    session.intervals_external_id = (
        f"opencoach:session:{session.id}"
    )
    session.intervals_event_id = "12345"
    session.intervals_sync_status = "synced"
    session.intervals_payload_hash = "old-hash"

    (
        service,
        repository,
        connections,
        client,
        factory_calls,
    ) = create_service([session])

    result = service.sync_period(
        athlete_profile_id=profile_id,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.synced == 1
    assert result.skipped == 0
    assert result.failed == 0

    assert connections.calls == [
        (
            profile_id,
            "intervals",
        )
    ]

    assert factory_calls == [
        (
            "secret-key",
            "i123456",
        )
    ]

    assert client.calls == []

    assert client.delete_calls == [
        [
            session.intervals_external_id,
        ]
    ]

    assert (
        session.intervals_sync_status
        == "deleted"
    )
    assert (
        session.intervals_last_synced_at
        == SYNCED_AT
    )
    assert session.intervals_sync_error is None

    assert [
        status
        for _, _, status in repository.saved
    ] == [
        "deleted",
    ]


def test_already_deleted_non_planned_session_is_skipped():
    session = make_session(
        status="skipped",
    )

    session.intervals_external_id = (
        f"opencoach:session:{session.id}"
    )
    session.intervals_event_id = "12345"
    session.intervals_sync_status = "deleted"

    (
        service,
        repository,
        connections,
        client,
        factory_calls,
    ) = create_service([session])

    result = service.sync_period(
        athlete_profile_id=uuid4(),
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert result.synced == 0
    assert result.skipped == 1
    assert result.failed == 0

    assert repository.saved == []
    assert connections.calls == []
    assert factory_calls == []

    assert client.calls == []
    assert client.delete_calls == []

    assert (
        session.intervals_sync_status
        == "deleted"
    )


def test_delete_failure_marks_session_failed():
    profile_id = uuid4()

    session = make_session(
        status="skipped",
    )

    session.intervals_external_id = (
        f"opencoach:session:{session.id}"
    )
    session.intervals_event_id = "12345"
    session.intervals_sync_status = "synced"

    client = FakeClient(
        error=RuntimeError(
            "delete unavailable"
        )
    )

    (
        service,
        repository,
        connections,
        returned_client,
        factory_calls,
    ) = create_service(
        [session],
        client=client,
    )

    result = service.sync_period(
        athlete_profile_id=profile_id,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    assert returned_client is client

    assert result.synced == 0
    assert result.skipped == 0
    assert result.failed == 1

    assert client.calls == []

    assert client.delete_calls == [
        [
            session.intervals_external_id,
        ]
    ]

    assert (
        session.intervals_sync_status
        == "failed"
    )
    assert (
        session.intervals_sync_error
        == "delete unavailable"
    )

    assert [
        status
        for _, _, status in repository.saved
    ] == [
        "failed",
    ]

    assert connections.calls == [
        (
            profile_id,
            "intervals",
        )
    ]

    assert factory_calls == [
        (
            "secret-key",
            "i123456",
        )
    ]

