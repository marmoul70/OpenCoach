"""Notification finale du workflow hebdomadaire OpenCoach.

Ce composant intervient uniquement après la persistance du débrief
et l'application du planning N+1.

Il ne clôture pas la semaine, ne recalcule pas le débrief et ne
génère aucune séance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Callable, Protocol
from uuid import UUID


class WeeklyDebriefNotificationStatus(str, Enum):
    """Résultat de la notification hebdomadaire."""

    SENT = "sent"
    ALREADY_SENT = "already_sent"
    NOT_READY = "not_ready"
    NO_DEBRIEF = "no_debrief"
    NO_RECIPIENT = "no_recipient"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WeeklyDebriefNotificationResult:
    """Résultat observable du finaliseur de notification."""

    athlete_profile_id: UUID
    status: WeeklyDebriefNotificationStatus
    sync_incomplete: bool = False
    error: str | None = None


class WeeklyDebriefRepository(Protocol):
    """Contrat minimal de persistance utilisé par le finaliseur."""

    def get_for_week(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ):
        ...

    def mark_notification_sent(
        self,
        athlete_profile_id: UUID,
        week_start: date,
        *,
        timestamp: datetime | None = None,
    ):
        ...


class TrainingSessionReader(Protocol):
    """Lecture minimale des séances de la semaine N+1."""

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ):
        ...


class WeeklyPushService(Protocol):
    """Port vers le système Push OpenCoach existant."""

    def send_weekly_debrief_notification(
        self,
        *,
        user_id: UUID,
        title: str,
        body: str,
        url: str = "/training",
    ):
        ...


class WeeklyDebriefNotificationService:
    """Finalise un workflow hebdomadaire par une notification Push."""

    def __init__(
        self,
        *,
        debrief_repository: WeeklyDebriefRepository,
        training_session_reader: TrainingSessionReader,
        push_service: WeeklyPushService,
        user_id_resolver: Callable[[UUID], UUID | None],
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._debrief_repository = debrief_repository
        self._training_session_reader = training_session_reader
        self._push_service = push_service
        self._user_id_resolver = user_id_resolver
        self._now = now or (
            lambda: datetime.now(timezone.utc)
        )

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> WeeklyDebriefNotificationResult:
        """Envoie au plus une notification pour un débrief prêt."""

        stored = self._debrief_repository.get_for_week(
            athlete_profile_id,
            week_start,
        )

        if stored is None:
            return WeeklyDebriefNotificationResult(
                athlete_profile_id=athlete_profile_id,
                status=WeeklyDebriefNotificationStatus.NO_DEBRIEF,
            )

        if stored.notification_sent_at is not None:
            return WeeklyDebriefNotificationResult(
                athlete_profile_id=athlete_profile_id,
                status=(
                    WeeklyDebriefNotificationStatus.ALREADY_SENT
                ),
            )

        if stored.planning_updated_at is None:
            return WeeklyDebriefNotificationResult(
                athlete_profile_id=athlete_profile_id,
                status=WeeklyDebriefNotificationStatus.NOT_READY,
            )

        user_id = self._user_id_resolver(
            athlete_profile_id
        )

        if user_id is None:
            return WeeklyDebriefNotificationResult(
                athlete_profile_id=athlete_profile_id,
                status=WeeklyDebriefNotificationStatus.FAILED,
                error="user_not_found",
            )

        next_week_start = week_start + timedelta(days=7)
        next_week_end = next_week_start + timedelta(days=6)

        sessions = (
            self._training_session_reader
            .list_sessions_between(
                athlete_profile_id,
                next_week_start,
                next_week_end,
            )
        )

        sync_incomplete = any(
            getattr(
                session,
                "intervals_sync_status",
                None,
            )
            == "failed"
            for session in sessions
        )

        if sync_incomplete:
            title = "Programme hebdomadaire prêt"
            body = (
                "Ta semaine a été analysée et ton programme "
                "est prêt. Certaines séances n'ont pas pu "
                "être synchronisées avec Intervals.icu."
            )
        else:
            title = "Programme hebdomadaire prêt"
            body = (
                "Ta semaine a été analysée. Ton programme "
                "de la semaine prochaine est prêt et "
                "synchronisé avec Intervals.icu."
            )

        try:
            report = (
                self._push_service
                .send_weekly_debrief_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    url="/training",
                )
            )
        except Exception as exc:
            return WeeklyDebriefNotificationResult(
                athlete_profile_id=athlete_profile_id,
                status=WeeklyDebriefNotificationStatus.FAILED,
                sync_incomplete=sync_incomplete,
                error=f"{type(exc).__name__}: {exc}",
            )

        if report.failed:
            return WeeklyDebriefNotificationResult(
                athlete_profile_id=athlete_profile_id,
                status=WeeklyDebriefNotificationStatus.FAILED,
                sync_incomplete=sync_incomplete,
                error=(
                    "push_delivery_failed:"
                    f"{report.failed}"
                ),
            )

        if report.sent == 0:
            return WeeklyDebriefNotificationResult(
                athlete_profile_id=athlete_profile_id,
                status=(
                    WeeklyDebriefNotificationStatus.NO_RECIPIENT
                ),
                sync_incomplete=sync_incomplete,
            )

        marked = (
            self._debrief_repository
            .mark_notification_sent(
                athlete_profile_id,
                week_start,
                timestamp=self._now(),
            )
        )

        if marked is None:
            return WeeklyDebriefNotificationResult(
                athlete_profile_id=athlete_profile_id,
                status=WeeklyDebriefNotificationStatus.FAILED,
                sync_incomplete=sync_incomplete,
                error="debrief_not_found_when_marking",
            )

        return WeeklyDebriefNotificationResult(
            athlete_profile_id=athlete_profile_id,
            status=WeeklyDebriefNotificationStatus.SENT,
            sync_incomplete=sync_incomplete,
        )
