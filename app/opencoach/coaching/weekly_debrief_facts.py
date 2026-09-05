"""Construction des faits du débrief hebdomadaire.

Ce module consolide les faits observables nécessaires au bilan
hebdomadaire.

Il reste volontairement indépendant de SQLAlchemy : les données
complémentaires issues du plan et des analyses d'exécution sont
résolues par la couche applicative puis injectées ici.
"""

from __future__ import annotations

from datetime import date
from typing import Mapping, Protocol
from uuid import UUID

from opencoach.coaching.weekly_debrief import (
    WeeklyDebriefFacts,
)


class WeeklyTrainingSession(Protocol):
    """Vue minimale d'une séance utile au bilan."""

    id: UUID
    status: str
    duration_minutes: int
    activity_id: UUID | None


class WeeklyActivity(Protocol):
    """Vue minimale d'une activité utile au bilan."""

    id: UUID
    moving_time_seconds: int | None
    elapsed_time_seconds: int | None
    training_load: float | None


class WeeklyTrainingPlanSnapshot(Protocol):
    """Vue minimale du plan hebdomadaire persistant."""

    target_load: float | None


class WeeklyExecutionAnalysis(Protocol):
    """Vue minimale d'une analyse d'exécution persistée."""

    training_session_id: UUID
    overall_status: str
    technical_status: str | None


class WeeklyTrainingSessionReader(Protocol):
    """Source des séances d'une semaine."""

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[WeeklyTrainingSession]:
        ...


class WeeklyActivityReader(Protocol):
    """Source des activités d'une semaine."""

    def list_activities_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[WeeklyActivity]:
        ...


def _actual_duration_minutes(
    activity: WeeklyActivity,
) -> float:
    """Retourne la meilleure durée réelle disponible."""

    seconds = activity.moving_time_seconds

    if seconds is None:
        seconds = activity.elapsed_time_seconds

    if seconds is None:
        return 0.0

    return max(
        float(seconds) / 60.0,
        0.0,
    )


def _resolve_intensity_counts(
    analyses: tuple[WeeklyExecutionAnalysis, ...],
) -> tuple[int, int]:
    """Compte les analyses exploitables et pleinement conformes.

    ``compliant`` est une conformité pleine.

    ``partial`` et ``non_compliant`` sont analysés mais ne comptent
    pas comme pleinement conformes.

    ``not_applicable`` et ``insufficient_data`` restent neutres et
    ne pénalisent donc pas artificiellement l'athlète.
    """

    analyzed = 0
    compliant = 0

    for analysis in analyses:
        status = analysis.overall_status

        if status in {
            "not_applicable",
            "insufficient_data",
        }:
            continue

        if status not in {
            "compliant",
            "partial",
            "non_compliant",
        }:
            continue

        analyzed += 1

        if status == "compliant":
            compliant += 1

    return compliant, analyzed


def build_weekly_debrief_facts_from_history(
    *,
    athlete_profile_id: UUID,
    week_start: date,
    week_end: date,
    session_reader: WeeklyTrainingSessionReader,
    activity_reader: WeeklyActivityReader,
    weekly_plan: WeeklyTrainingPlanSnapshot | None = None,
    execution_analyses: (
        Mapping[UUID, WeeklyExecutionAnalysis] | None
    ) = None,
    key_session_ids: frozenset[UUID] = frozenset(),
) -> WeeklyDebriefFacts:
    """Consolide les faits historiques d'une semaine.

    Les séances représentent le plan réellement persisté.
    Les activités représentent l'exécution réelle.

    ``weekly_plan`` apporte la charge cible persistée.

    ``execution_analyses`` contient les analyses d'exécution déjà
    résolues par la couche applicative.

    ``key_session_ids`` provient explicitement du snapshot de
    planning : aucune heuristique n'est appliquée à ``planning_key``
    ou au titre de la séance.
    """

    if week_end < week_start:
        raise ValueError(
            "week_end doit être postérieur ou égal à week_start."
        )

    sessions = list(
        session_reader.list_sessions_between(
            athlete_profile_id,
            week_start,
            week_end,
        )
    )

    activities = list(
        activity_reader.list_activities_between(
            athlete_profile_id,
            week_start,
            week_end,
        )
    )

    planned_sessions = len(sessions)

    completed_sessions = sum(
        1
        for session in sessions
        if session.status == "completed"
    )

    skipped_sessions = sum(
        1
        for session in sessions
        if session.status == "skipped"
    )

    planned_duration_minutes = sum(
        max(
            int(session.duration_minutes),
            0,
        )
        for session in sessions
    )

    linked_activity_ids = {
        session.activity_id
        for session in sessions
        if session.activity_id is not None
    }

    supplementary_sessions = sum(
        1
        for activity in activities
        if activity.id not in linked_activity_ids
    )

    actual_duration_minutes = sum(
        _actual_duration_minutes(activity)
        for activity in activities
    )

    actual_load = sum(
        max(
            float(activity.training_load),
            0.0,
        )
        for activity in activities
        if activity.training_load is not None
    )

    planned_load = 0.0

    if (
        weekly_plan is not None
        and weekly_plan.target_load is not None
    ):
        planned_load = max(
            float(weekly_plan.target_load),
            0.0,
        )

    sessions_by_id = {
        session.id: session
        for session in sessions
        if getattr(session, "id", None) is not None
    }

    key_sessions_planned = sum(
        1
        for session_id in key_session_ids
        if session_id in sessions_by_id
    )

    key_sessions_completed = sum(
        1
        for session_id in key_session_ids
        if (
            session_id in sessions_by_id
            and sessions_by_id[session_id].status
            == "completed"
        )
    )

    relevant_analyses = tuple(
        analysis
        for session_id, analysis in (
            execution_analyses or {}
        ).items()
        if (
            session_id in sessions_by_id
            and sessions_by_id[session_id].status
            == "completed"
        )
    )

    (
        compliant_intensity_sessions,
        analyzed_intensity_sessions,
    ) = _resolve_intensity_counts(
        relevant_analyses
    )

    # Sémantique T6.5.1 conservée :
    # la confiance décrit la présence d'un historique observable,
    # pas la disponibilité de chaque source d'enrichissement.
    history_confidence = (
        1.0
        if sessions or activities
        else 0.0
    )

    return WeeklyDebriefFacts(
        week_start=week_start,
        week_end=week_end,
        planned_sessions=planned_sessions,
        completed_sessions=completed_sessions,
        skipped_sessions=skipped_sessions,
        supplementary_sessions=supplementary_sessions,
        planned_duration_minutes=planned_duration_minutes,
        actual_duration_minutes=round(
            actual_duration_minutes,
            2,
        ),
        planned_load=round(
            planned_load,
            2,
        ),
        actual_load=round(
            actual_load,
            2,
        ),
        key_sessions_planned=key_sessions_planned,
        key_sessions_completed=key_sessions_completed,
        compliant_intensity_sessions=(
            compliant_intensity_sessions
        ),
        analyzed_intensity_sessions=(
            analyzed_intensity_sessions
        ),
        history_confidence=history_confidence,
    )
