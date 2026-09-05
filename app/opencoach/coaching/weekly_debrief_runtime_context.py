"""Résolution des faits runtime du débrief hebdomadaire.

Cette couche traduit l'état persistant des séances et activités en
contexte temporel utilisable par l'orchestrateur T6.5.6.

Elle ne génère aucun planning et ne persiste rien.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID


class WeeklyRuntimeTrainingSession(Protocol):
    """Projection minimale d'une séance persistée."""

    id: UUID
    date: date
    status: str
    planning_importance: str | None
    activity_id: UUID | None


class WeeklyRuntimeActivity(Protocol):
    """Projection minimale d'une activité persistée."""

    id: UUID
    start_at: datetime
    moving_time_seconds: int | None
    elapsed_time_seconds: int | None


class WeeklyRuntimeSessionReader(Protocol):
    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[WeeklyRuntimeTrainingSession]:
        ...


class WeeklyRuntimeActivityReader(Protocol):
    def get_activity(
        self,
        athlete_profile_id: UUID,
        activity_id: UUID,
    ) -> WeeklyRuntimeActivity | None:
        ...


@dataclass(frozen=True, slots=True)
class WeeklyDebriefRuntimeFacts:
    """Faits runtime nécessaires à l'orchestration."""

    week_start: date
    week_end: date

    has_remaining_planned_session: bool

    completed_sessions_count: int

    last_completed_at: datetime | None

    key_session_ids: frozenset[UUID]


def resolve_week_bounds(
    reference_date: date,
) -> tuple[date, date]:
    """Retourne le lundi et le dimanche de la semaine."""

    week_start = (
        reference_date
        - timedelta(
            days=reference_date.weekday()
        )
    )

    return (
        week_start,
        week_start + timedelta(days=6),
    )


def _activity_end_at(
    activity: WeeklyRuntimeActivity,
) -> datetime:
    """Calcule la fin effective connue d'une activité."""

    seconds = activity.moving_time_seconds

    if seconds is None:
        seconds = activity.elapsed_time_seconds

    if seconds is None:
        seconds = 0

    seconds = max(
        int(seconds),
        0,
    )

    start_at = activity.start_at

    # SQLite restitue les colonnes DateTime sans tzinfo.
    # Dans le modèle Activity, start_at représente l'instant
    # absolu UTC ; start_at_local porte séparément l'heure locale.
    if start_at.tzinfo is None:
        start_at = start_at.replace(
            tzinfo=timezone.utc
        )

    return (
        start_at
        + timedelta(seconds=seconds)
    )


def build_weekly_debrief_runtime_facts(
    *,
    athlete_profile_id: UUID,
    reference_date: date,
    session_reader: WeeklyRuntimeSessionReader,
    activity_reader: WeeklyRuntimeActivityReader,
) -> WeeklyDebriefRuntimeFacts:
    """Construit le contexte réel de la semaine d'un athlète."""

    (
        week_start,
        week_end,
    ) = resolve_week_bounds(
        reference_date
    )

    sessions = list(
        session_reader.list_sessions_between(
            athlete_profile_id,
            week_start,
            week_end,
        )
    )

    has_remaining_planned_session = any(
        session.date == week_end
        and session.status == "planned"
        for session in sessions
    )

    completed_sessions_count = sum(
        session.status == "completed"
        for session in sessions
    )

    key_session_ids = frozenset(
        session.id
        for session in sessions
        if (
            session.planning_importance
            == "key"
        )
    )

    completed_ends: list[
        datetime
    ] = []

    for session in sessions:
        if (
            session.status != "completed"
            or session.activity_id is None
        ):
            continue

        activity = (
            activity_reader.get_activity(
                athlete_profile_id,
                session.activity_id,
            )
        )

        if activity is None:
            continue

        completed_ends.append(
            _activity_end_at(
                activity
            )
        )

    last_completed_at = (
        max(completed_ends)
        if completed_ends
        else None
    )

    return WeeklyDebriefRuntimeFacts(
        week_start=week_start,
        week_end=week_end,
        has_remaining_planned_session=(
            has_remaining_planned_session
        ),
        completed_sessions_count=(
            completed_sessions_count
        ),
        last_completed_at=(
            last_completed_at
        ),
        key_session_ids=(
            key_session_ids
        ),
    )
