"""Synchronisation des séances planifiées OpenCoach vers Intervals.icu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from typing import Callable, Protocol
from uuid import UUID

from opencoach.integrations.intervals.client import (
    IntervalsClient,
)
from opencoach.integrations.intervals.workout_mapper import (
    IntervalsWorkoutPayload,
    map_training_session_to_intervals,
)
from opencoach.models import TrainingSession
from opencoach.services.integration_connection import (
    IntegrationConnectionService,
)


class WorkoutSyncStatus(str, Enum):
    """Résultat individuel d'une synchronisation."""

    SYNCED = "synced"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WorkoutSyncItem:
    """Résultat de synchronisation d'une séance."""

    session_id: UUID
    status: WorkoutSyncStatus
    external_id: str | None = None
    event_id: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class WorkoutSyncResult:
    """Résultat agrégé d'une synchronisation de période."""

    items: tuple[WorkoutSyncItem, ...]

    @property
    def synced(self) -> int:
        return sum(
            item.status is WorkoutSyncStatus.SYNCED
            for item in self.items
        )

    @property
    def skipped(self) -> int:
        return sum(
            item.status is WorkoutSyncStatus.SKIPPED
            for item in self.items
        )

    @property
    def failed(self) -> int:
        return sum(
            item.status is WorkoutSyncStatus.FAILED
            for item in self.items
        )


class TrainingSessionSyncRepository(Protocol):
    """Contrat minimal requis par le service."""

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TrainingSession]:
        ...

    def save_session(
        self,
        athlete_profile_id: UUID,
        session: TrainingSession,
    ) -> TrainingSession:
        ...


ClientFactory = Callable[
    [str, str],
    IntervalsClient,
]


def _default_client_factory(
    api_key: str,
    athlete_id: str,
) -> IntervalsClient:
    return IntervalsClient(
        api_key=api_key,
        athlete_id=athlete_id,
    )


class IntervalsWorkoutSyncService:
    """Synchronise les séances planifiées d'un profil athlète."""

    def __init__(
        self,
        *,
        repository: TrainingSessionSyncRepository,
        connection_service: IntegrationConnectionService,
        client_factory: ClientFactory = _default_client_factory,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.connection_service = connection_service
        self.client_factory = client_factory
        self.now = now or (
            lambda: datetime.now(timezone.utc)
        )

    def sync_period(
        self,
        *,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> WorkoutSyncResult:
        """Synchronise les séances planifiées d'une période.

        - une séance non exportable est ignorée ;
        - un hash déjà synchronisé est ignoré ;
        - les autres séances sont envoyées en un seul bulk upsert ;
        - chaque résultat est persisté sur sa TrainingSession.
        """

        sessions = self.repository.list_sessions_between(
            athlete_profile_id,
            start_date,
            end_date,
        )

        immediate_results: list[
            WorkoutSyncItem
        ] = []

        candidates: list[
            tuple[
                TrainingSession,
                IntervalsWorkoutPayload,
                str,
            ]
        ] = []

        delete_candidates: list[
            TrainingSession
        ] = []

        for session in sessions:
            if session.id is None:
                continue

            if session.status != "planned":
                if (
                    session.intervals_external_id
                    and session.intervals_sync_status
                    != "deleted"
                ):
                    delete_candidates.append(
                        session
                    )
                    continue

                immediate_results.append(
                    WorkoutSyncItem(
                        session_id=session.id,
                        status=WorkoutSyncStatus.SKIPPED,
                        external_id=(
                            session.intervals_external_id
                        ),
                        event_id=(
                            session.intervals_event_id
                        ),
                    )
                )
                continue

            payload = (
                map_training_session_to_intervals(
                    session
                )
            )

            if payload is None:
                immediate_results.append(
                    WorkoutSyncItem(
                        session_id=session.id,
                        status=WorkoutSyncStatus.SKIPPED,
                    )
                )
                continue

            payload_hash = payload.payload_hash()

            if (
                session.intervals_sync_status
                == "synced"
                and session.intervals_payload_hash
                == payload_hash
            ):
                immediate_results.append(
                    WorkoutSyncItem(
                        session_id=session.id,
                        status=WorkoutSyncStatus.SKIPPED,
                        external_id=(
                            payload.external_id
                        ),
                        event_id=(
                            session.intervals_event_id
                        ),
                    )
                )
                continue

            session.intervals_external_id = (
                payload.external_id
            )
            session.intervals_sync_status = "pending"
            session.intervals_sync_error = None

            self.repository.save_session(
                athlete_profile_id,
                session,
            )

            candidates.append(
                (
                    session,
                    payload,
                    payload_hash,
                )
            )

        if delete_candidates:
            try:
                delete_credentials = (
                    self.connection_service
                    .get_credentials(
                        athlete_profile_id,
                        "intervals",
                    )
                )

                delete_client = (
                    self.client_factory(
                        delete_credentials.secret,
                        delete_credentials.athlete_id,
                    )
                )

                delete_client.delete_workouts(
                    [
                        session.intervals_external_id
                        for session
                        in delete_candidates
                        if session.intervals_external_id
                    ]
                )

            except Exception as exc:
                error = (
                    str(exc)
                    or exc.__class__.__name__
                )

                for session in delete_candidates:
                    session.intervals_sync_status = (
                        "failed"
                    )
                    session.intervals_sync_error = (
                        error
                    )

                    self.repository.save_session(
                        athlete_profile_id,
                        session,
                    )

                    immediate_results.append(
                        WorkoutSyncItem(
                            session_id=session.id,
                            status=(
                                WorkoutSyncStatus.FAILED
                            ),
                            external_id=(
                                session
                                .intervals_external_id
                            ),
                            event_id=(
                                session
                                .intervals_event_id
                            ),
                            error=error,
                        )
                    )

            else:
                synced_at = self.now()

                for session in delete_candidates:
                    session.intervals_sync_status = (
                        "deleted"
                    )
                    session.intervals_sync_error = (
                        None
                    )
                    session.intervals_last_synced_at = (
                        synced_at
                    )

                    self.repository.save_session(
                        athlete_profile_id,
                        session,
                    )

                    immediate_results.append(
                        WorkoutSyncItem(
                            session_id=session.id,
                            status=(
                                WorkoutSyncStatus.SYNCED
                            ),
                            external_id=(
                                session
                                .intervals_external_id
                            ),
                            event_id=(
                                session
                                .intervals_event_id
                            ),
                        )
                    )

        if not candidates:
            return WorkoutSyncResult(
                items=tuple(immediate_results)
            )

        try:
            credentials = (
                self.connection_service
                .get_credentials(
                    athlete_profile_id,
                    "intervals",
                )
            )

            client = self.client_factory(
                credentials.secret,
                credentials.athlete_id,
            )

            response = client.upsert_workouts(
                [
                    payload.as_dict()
                    for _, payload, _ in candidates
                ]
            )

        except Exception as exc:
            error = str(exc) or exc.__class__.__name__

            failed_results = []

            for session, payload, _ in candidates:
                session.intervals_sync_status = (
                    "failed"
                )
                session.intervals_sync_error = error

                self.repository.save_session(
                    athlete_profile_id,
                    session,
                )

                failed_results.append(
                    WorkoutSyncItem(
                        session_id=session.id,
                        status=WorkoutSyncStatus.FAILED,
                        external_id=(
                            payload.external_id
                        ),
                        error=error,
                    )
                )

            return WorkoutSyncResult(
                items=tuple(
                    immediate_results
                    + failed_results
                )
            )

        events_by_external_id: dict[
            str,
            dict,
        ] = {}

        for event in response:
            external_id = event.get(
                "external_id"
            )

            if external_id is not None:
                events_by_external_id[
                    str(external_id)
                ] = event

        completed_results = []

        for (
            session,
            payload,
            payload_hash,
        ) in candidates:
            event = events_by_external_id.get(
                payload.external_id
            )

            if event is None:
                error = (
                    "Intervals.icu n'a pas retourné "
                    "l'événement synchronisé."
                )

                session.intervals_sync_status = (
                    "failed"
                )
                session.intervals_sync_error = error

                self.repository.save_session(
                    athlete_profile_id,
                    session,
                )

                completed_results.append(
                    WorkoutSyncItem(
                        session_id=session.id,
                        status=WorkoutSyncStatus.FAILED,
                        external_id=(
                            payload.external_id
                        ),
                        error=error,
                    )
                )
                continue

            raw_event_id = event.get("id")

            event_id = (
                str(raw_event_id)
                if raw_event_id is not None
                else None
            )

            synced_at = self.now()

            session.intervals_external_id = (
                payload.external_id
            )
            session.intervals_event_id = event_id
            session.intervals_sync_status = "synced"
            session.intervals_last_synced_at = (
                synced_at
            )
            session.intervals_payload_hash = (
                payload_hash
            )
            session.intervals_sync_error = None

            self.repository.save_session(
                athlete_profile_id,
                session,
            )

            completed_results.append(
                WorkoutSyncItem(
                    session_id=session.id,
                    status=WorkoutSyncStatus.SYNCED,
                    external_id=(
                        payload.external_id
                    ),
                    event_id=event_id,
                )
            )

        return WorkoutSyncResult(
            items=tuple(
                immediate_results
                + completed_results
            )
        )
