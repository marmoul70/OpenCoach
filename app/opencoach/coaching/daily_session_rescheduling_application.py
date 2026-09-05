"""Application d'une proposition de report quotidien.

La séance source ``skipped`` reste immuable dans l'historique.
L'acceptation crée une nouvelle occurrence ``planned`` sur le
créneau actuellement recommandé par le moteur de placement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID
from typing import Protocol

from opencoach.coaching.daily_session_rescheduling_service import (
    DailySessionReschedulingService,
)
from opencoach.coaching.generation.identity import (
    build_planning_key,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    AthleteProfile,
    TrainingSession,
)


class DailySessionReschedulingApplicationError(
    RuntimeError
):
    """Erreur métier pendant l'application d'un report."""


class DailySessionReschedulingSourceNotFoundError(
    DailySessionReschedulingApplicationError
):
    """La séance source n'existe pas."""


class DailySessionReschedulingInvalidSourceError(
    DailySessionReschedulingApplicationError
):
    """La séance source ne peut pas être reportée."""


class DailySessionReschedulingUnavailableError(
    DailySessionReschedulingApplicationError
):
    """Aucun report valide n'est actuellement disponible."""


@dataclass(frozen=True, slots=True)
class DailySessionReschedulingApplicationResult:
    """Résultat de l'acceptation d'un report."""

    source_session: TrainingSession
    rescheduled_session: TrainingSession

    created: bool




class DailyWorkoutSyncService(Protocol):
    """Port de synchronisation externe du planning."""

    def sync_period(
        self,
        *,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> object:
        """Synchronise une période de planning."""
        ...


@dataclass(slots=True)
class DailySessionReschedulingApplicationService:
    """Applique explicitement une proposition de report."""

    training_session_repository: TrainingSessionRepository

    rescheduling_service: DailySessionReschedulingService

    workout_sync_service: (
        DailyWorkoutSyncService | None
    ) = None

    def apply(
        self,
        *,
        athlete_profile_id: UUID,
        athlete: AthleteProfile,
        source_session_id: UUID,
    ) -> DailySessionReschedulingApplicationResult:
        """Crée la nouvelle occurrence proposée par le coach."""

        source = (
            self.training_session_repository
            .get_session(
                athlete_profile_id,
                source_session_id,
            )
        )

        if source is None:
            raise (
                DailySessionReschedulingSourceNotFoundError(
                    "Séance source introuvable."
                )
            )

        if source.status != "skipped":
            raise (
                DailySessionReschedulingInvalidSourceError(
                    "Seule une séance annulée peut être reportée."
                )
            )

        proposal = (
            self.rescheduling_service.propose(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                athlete=athlete,
                session=source,
            )
        )

        if proposal is None:
            raise (
                DailySessionReschedulingUnavailableError(
                    "Aucun créneau de report valide "
                    "n'est actuellement disponible."
                )
            )

        target_date = (
            proposal.suggested_date
        )

        if target_date <= source.date:
            raise (
                DailySessionReschedulingUnavailableError(
                    "Le report doit être situé après "
                    "la séance annulée."
                )
            )

        week_start = (
            target_date
            - timedelta(
                days=target_date.weekday(),
            )
        )

        week_end = (
            week_start
            + timedelta(
                days=6,
            )
        )

        planning_key = build_planning_key(
            week_start=week_start,
            slot_id=(
                f"rescheduled-{source.id}"
            ),
        )

        existing_sessions = (
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                week_start,
                week_end,
            )
        )

        existing = next(
            (
                session
                for session
                in existing_sessions
                if (
                    session.planning_key
                    == planning_key
                )
            ),
            None,
        )

        if existing is not None:
            return (
                DailySessionReschedulingApplicationResult(
                    source_session=source,
                    rescheduled_session=existing,
                    created=False,
                )
            )

        rescheduled = TrainingSession(
            id=None,
            date=target_date,
            type=source.type,
            sport_type=source.sport_type,
            planning_importance=(
                source.planning_importance
            ),
            title=source.title,
            description=source.description,
            duration_minutes=(
                source.duration_minutes
            ),
            planning_key=planning_key,
            distance_km=source.distance_km,
            elevation_gain_m=(
                source.elevation_gain_m
            ),
            intensity=source.intensity,
            heart_rate_zone=(
                source.heart_rate_zone
            ),
            status="planned",
            activity_id=None,
        )

        saved = (
            self.training_session_repository
            .save_session(
                athlete_profile_id,
                rescheduled,
            )
        )

        self._sync_replanning_best_effort(
            athlete_profile_id=athlete_profile_id,
            source=source,
            applied=saved,
        )

        return (
            DailySessionReschedulingApplicationResult(
                source_session=source,
                rescheduled_session=saved,
                created=True,
            )
        )

    def _sync_replanning_best_effort(
        self,
        *,
        athlete_profile_id: UUID,
        source: TrainingSession,
        applied: TrainingSession,
    ) -> None:
        """Synchronise le delta sans invalider OpenCoach."""

        if self.workout_sync_service is None:
            return

        start_date = min(
            source.date,
            applied.date,
        )
        end_date = max(
            source.date,
            applied.date,
        )

        try:
            self.workout_sync_service.sync_period(
                athlete_profile_id=athlete_profile_id,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception:
            # La décision locale est déjà persistée.
            # Une panne Intervals reste best-effort.
            return
