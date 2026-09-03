from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from typing import Callable
from uuid import UUID

from opencoach.integrations.intervals import IntervalsSyncService
from opencoach.services.integration_connection import (
    IntegrationConnectionService,
)


DEFAULT_SYNC_DAYS = 30
INITIAL_SYNC_DAYS = 90
DEFAULT_INCREMENTAL_LOOKBACK_DAYS = 2


@dataclass(frozen=True, slots=True)
class IntervalsSyncResult:
    """Résultat structuré d'une synchronisation Intervals.icu."""

    synced_activities: int
    synced_wellness_days: int

    oldest: date
    newest: date

    synced_at: datetime

    def __post_init__(self) -> None:
        if self.synced_activities < 0:
            raise ValueError(
                "Le nombre d'activités synchronisées "
                "ne peut pas être négatif."
            )

        if self.synced_wellness_days < 0:
            raise ValueError(
                "Le nombre de jours Wellness synchronisés "
                "ne peut pas être négatif."
            )

        if self.oldest > self.newest:
            raise ValueError(
                "La date de début de synchronisation "
                "ne peut pas être postérieure à la date de fin."
            )


class IntervalsInitialSyncAlreadyCompletedError(
    RuntimeError
):
    """La synchronisation initiale a déjà été réalisée."""


class IntervalsApplicationService:
    """Service applicatif de synchronisation Intervals.icu."""

    def __init__(
        self,
        sync_service: IntervalsSyncService,
        connection_service: IntegrationConnectionService | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.sync_service = sync_service
        self.connection_service = connection_service
        self.clock = (
            clock
            if clock is not None
            else lambda: datetime.now(timezone.utc)
        )

    def sync_activities(
        self,
        athlete_profile_id: UUID,
        *,
        newest: date | None = None,
        days: int = DEFAULT_SYNC_DAYS,
    ) -> int:
        """Synchronise les activités récentes d'un athlète."""

        oldest, newest = self._resolve_period(
            newest=newest,
            days=days,
        )

        return self.sync_service.sync_activities(
            athlete_profile_id=athlete_profile_id,
            oldest=oldest,
            newest=newest,
        )

    def sync_wellness(
        self,
        athlete_profile_id: UUID,
        *,
        newest: date | None = None,
        days: int = DEFAULT_SYNC_DAYS,
    ) -> int:
        """Synchronise les données Wellness récentes."""

        oldest, newest = self._resolve_period(
            newest=newest,
            days=days,
        )

        return self.sync_service.sync_wellness(
            athlete_profile_id=athlete_profile_id,
            oldest=oldest,
            newest=newest,
        )

    def sync_initial_history(
        self,
        athlete_profile_id: UUID,
        *,
        newest: date | None = None,
        days: int = INITIAL_SYNC_DAYS,
    ) -> IntervalsSyncResult:
        """Importe l'historique initial Intervals.icu.

        Cette opération est réservée à la toute première
        synchronisation de l'intégration.

        Une connexion possédant déjà un ``last_synced_at``
        ne peut plus relancer ce bootstrap.
        """

        if self.connection_service is None:
            raise RuntimeError(
                "connection_service est requis pour "
                "la synchronisation initiale."
            )

        if days <= 0:
            raise ValueError(
                "days doit être strictement positif."
            )

        connection = (
            self.connection_service.get_connection(
                athlete_profile_id,
                "intervals",
            )
        )

        if connection is None:
            raise RuntimeError(
                "La connexion Intervals.icu "
                "n'est pas configurée."
            )

        if connection.last_synced_at is not None:
            raise IntervalsInitialSyncAlreadyCompletedError(
                "La synchronisation initiale "
                "Intervals.icu a déjà été effectuée."
            )

        return self.sync_all(
            athlete_profile_id,
            newest=newest,
            days=days,
        )


    def sync_incremental(
        self,
        athlete_profile_id: UUID,
        *,
        newest: date | None = None,
        initial_days: int = DEFAULT_SYNC_DAYS,
        lookback_days: int = DEFAULT_INCREMENTAL_LOOKBACK_DAYS,
    ) -> IntervalsSyncResult:
        """Synchronise depuis le dernier état connu.

        Une petite fenêtre de sécurité est relue avant la dernière
        synchronisation afin d'absorber les activités ou modifications
        arrivées tardivement chez le fournisseur.

        Sans synchronisation précédente, la fenêtre initiale standard
        est utilisée.
        """

        if self.connection_service is None:
            raise RuntimeError(
                "connection_service est requis pour "
                "une synchronisation incrémentale."
            )

        if initial_days <= 0:
            raise ValueError(
                "initial_days doit être strictement positif."
            )

        if lookback_days < 0:
            raise ValueError(
                "lookback_days ne peut pas être négatif."
            )

        resolved_newest = (
            newest
            if newest is not None
            else date.today()
        )

        connection = (
            self.connection_service.get_connection(
                athlete_profile_id,
                "intervals",
            )
        )

        last_synced_at = connection.last_synced_at

        if last_synced_at is None:
            oldest = (
                resolved_newest
                - timedelta(
                    days=initial_days,
                )
            )
        else:
            oldest = (
                last_synced_at.date()
                - timedelta(
                    days=lookback_days,
                )
            )

        return self.sync_all(
            athlete_profile_id,
            newest=resolved_newest,
            days=(
                resolved_newest - oldest
            ).days,
        )

    def sync_all(
        self,
        athlete_profile_id: UUID,
        *,
        newest: date | None = None,
        days: int = DEFAULT_SYNC_DAYS,
    ) -> IntervalsSyncResult:
        """Synchronise activités et Wellness sur la même période.

        La date de dernière synchronisation n'est enregistrée
        qu'après le succès complet des deux synchronisations.
        """

        oldest, newest = self._resolve_period(
            newest=newest,
            days=days,
        )

        synced_activities = (
            self.sync_service.sync_activities(
                athlete_profile_id=athlete_profile_id,
                oldest=oldest,
                newest=newest,
            )
        )

        synced_wellness = (
            self.sync_service.sync_wellness(
                athlete_profile_id=athlete_profile_id,
                oldest=oldest,
                newest=newest,
            )
        )

        synced_at = self.clock()

        if self.connection_service is not None:
            self.connection_service.mark_synced(
                athlete_profile_id,
                "intervals",
                synced_at,
            )

        return IntervalsSyncResult(
            synced_activities=synced_activities,
            synced_wellness_days=synced_wellness,
            oldest=oldest,
            newest=newest,
            synced_at=synced_at,
        )

    @staticmethod
    def _resolve_period(
        *,
        newest: date | None,
        days: int,
    ) -> tuple[date, date]:
        if days < 1:
            raise ValueError(
                "La période de synchronisation doit être positive."
            )

        if newest is None:
            newest = date.today()

        oldest = newest - timedelta(days=days)

        return oldest, newest
