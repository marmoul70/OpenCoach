"""Application d'un choix de replanification quotidienne.

La séance source annulée reste immuable dans l'historique.

Avant toute écriture, le service recalcule les options actuellement
valides afin d'éviter l'application d'une proposition devenue obsolète.

Actions supportées :

- cancel : aucune nouvelle séance ;
- move_unchanged : création d'une occurrence identique ;
- move_adapted : création de la variante adaptée calculée par OpenCoach.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from opencoach.coaching.daily_session_replanning import (
    DailyReplanningAction,
    DailySessionReplanningOption,
)
from opencoach.coaching.daily_session_replanning_service import (
    DailySessionReplanningService,
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


class DailySessionReplanningApplicationError(
    RuntimeError
):
    """Erreur métier pendant l'application d'une replanification."""


class DailySessionReplanningSourceNotFoundError(
    DailySessionReplanningApplicationError
):
    """La séance source n'existe pas."""


class DailySessionReplanningInvalidSourceError(
    DailySessionReplanningApplicationError
):
    """La séance source ne peut pas être replanifiée."""


class DailySessionReplanningOptionUnavailableError(
    DailySessionReplanningApplicationError
):
    """L'option demandée n'est plus disponible."""


@dataclass(
    frozen=True,
    slots=True,
)
class DailySessionReplanningApplicationResult:
    """Résultat de l'application du choix de l'athlète."""

    source_session: TrainingSession

    action: DailyReplanningAction

    applied_session: TrainingSession | None

    created: bool

    cancelled: bool


@dataclass(slots=True)
class DailySessionReplanningApplicationService:
    """Applique explicitement une option recalculée."""

    training_session_repository: (
        TrainingSessionRepository
    )

    replanning_service: (
        DailySessionReplanningService
    )

    def apply(
        self,
        *,
        athlete_profile_id: UUID,
        athlete: AthleteProfile,
        source_session_id: UUID,
        action: DailyReplanningAction,
        target_date: date | None = None,
    ) -> DailySessionReplanningApplicationResult:
        """Applique une option encore valide."""

        source = (
            self.training_session_repository
            .get_session(
                athlete_profile_id,
                source_session_id,
            )
        )

        if source is None:
            raise (
                DailySessionReplanningSourceNotFoundError(
                    "Séance source introuvable."
                )
            )

        if source.status != "skipped":
            raise (
                DailySessionReplanningInvalidSourceError(
                    "Seule une séance annulée peut être replanifiée."
                )
            )

        if source.activity_id is not None:
            raise (
                DailySessionReplanningInvalidSourceError(
                    "Une séance liée à une activité "
                    "ne peut pas être replanifiée."
                )
            )

        # ----------------------------------------------------
        # Idempotence
        # ----------------------------------------------------
        #
        # Une séance déjà créée depuis cette source doit être
        # retournée avant de recalculer les options.
        #
        # La nouvelle occurrence fait désormais partie du
        # planning hebdomadaire et peut légitimement modifier
        # le classement des candidats. Recalculer d'abord la
        # proposition casserait donc l'idempotence.
        #
        if (
            action
            is not DailyReplanningAction.CANCEL
        ):
            existing = (
                self._find_existing_replanned_session(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    source=source,
                )
            )

            if existing is not None:
                return (
                    DailySessionReplanningApplicationResult(
                        source_session=source,
                        action=action,
                        applied_session=existing,
                        created=False,
                        cancelled=False,
                    )
                )

        proposal = (
            self.replanning_service.propose(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                athlete=athlete,
                session=source,
            )
        )

        if proposal is None:
            raise (
                DailySessionReplanningOptionUnavailableError(
                    "Aucune option de replanification "
                    "n'est actuellement disponible."
                )
            )

        option = (
            self._find_requested_option(
                proposal_options=(
                    proposal.options
                ),
                action=action,
                target_date=target_date,
            )
        )

        if action is DailyReplanningAction.CANCEL:
            return (
                DailySessionReplanningApplicationResult(
                    source_session=source,
                    action=action,
                    applied_session=None,
                    created=False,
                    cancelled=True,
                )
            )

        if option.session is None:
            raise (
                DailySessionReplanningOptionUnavailableError(
                    "L'option de déplacement ne contient "
                    "aucune séance applicable."
                )
            )

        if option.target_date is None:
            raise (
                DailySessionReplanningOptionUnavailableError(
                    "L'option de déplacement ne contient "
                    "aucune date cible."
                )
            )

        if option.target_date <= source.date:
            raise (
                DailySessionReplanningOptionUnavailableError(
                    "La séance replanifiée doit être située "
                    "après la séance annulée."
                )
            )

        return self._apply_move(
            athlete_profile_id=(
                athlete_profile_id
            ),
            source=source,
            option=option,
        )

    @staticmethod
    def _find_requested_option(
        *,
        proposal_options: tuple[
            DailySessionReplanningOption,
            ...,
        ],
        action: DailyReplanningAction,
        target_date: date | None,
    ) -> DailySessionReplanningOption:
        """Retrouve exactement l'option choisie."""

        matches = tuple(
            option
            for option in proposal_options
            if (
                option.action is action
                and (
                    action
                    is DailyReplanningAction.CANCEL
                    or (
                        target_date is not None
                        and option.target_date
                        == target_date
                    )
                )
            )
        )

        if len(matches) != 1:
            raise (
                DailySessionReplanningOptionUnavailableError(
                    "L'option choisie n'est plus disponible. "
                    "Le planning doit être recalculé."
                )
            )

        return matches[0]

    def _find_existing_replanned_session(
        self,
        *,
        athlete_profile_id: UUID,
        source: TrainingSession,
    ) -> TrainingSession | None:
        """Recherche une occurrence déjà créée depuis la source."""

        week_start = (
            source.date
            - timedelta(
                days=source.date.weekday(),
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
                f"replanned-{source.id}"
            ),
        )

        sessions = (
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                week_start,
                week_end,
            )
        )

        return next(
            (
                session
                for session in sessions
                if (
                    session.planning_key
                    == planning_key
                )
            ),
            None,
        )


    def _apply_move(
        self,
        *,
        athlete_profile_id: UUID,
        source: TrainingSession,
        option: DailySessionReplanningOption,
    ) -> DailySessionReplanningApplicationResult:
        """Crée l'occurrence correspondant au choix validé."""

        assert option.target_date is not None
        assert option.session is not None

        target_date = option.target_date

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
                f"replanned-{source.id}"
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
                DailySessionReplanningApplicationResult(
                    source_session=source,
                    action=option.action,
                    applied_session=existing,
                    created=False,
                    cancelled=False,
                )
            )

        template = option.session

        replanned = TrainingSession(
            id=None,
            date=target_date,
            type=template.type,
            sport_type=template.sport_type,
            title=template.title,
            description=template.description,
            duration_minutes=(
                template.duration_minutes
            ),
            planning_key=planning_key,
            distance_km=template.distance_km,
            elevation_gain_m=(
                template.elevation_gain_m
            ),
            intensity=template.intensity,
            heart_rate_zone=(
                template.heart_rate_zone
            ),
            status="planned",
            activity_id=None,
        )

        saved = (
            self.training_session_repository
            .save_session(
                athlete_profile_id,
                replanned,
            )
        )

        return (
            DailySessionReplanningApplicationResult(
                source_session=source,
                action=option.action,
                applied_session=saved,
                created=True,
                cancelled=False,
            )
        )
