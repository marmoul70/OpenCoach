"""Recherche et lecture détaillée des activités d'un athlète."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.database.repositories import ActivityDetailRepository, ActivityRepository
from opencoach.models import Activity, ActivityDetail


@dataclass(frozen=True, slots=True)
class ActivityDetailResult:
    """Résultat métier d'une sélection d'activité."""

    status: str
    activity: Activity | None = None
    detail: ActivityDetail | None = None
    choices: tuple[Activity, ...] = ()
    choices_truncated: bool = False
    selection_activity_id: UUID | None = None
    selection_date: date | None = None


class ActivityDetailService:
    """Résout une activité de l'athlète et charge son détail centralisé."""

    def __init__(
        self,
        activity_repository: ActivityRepository,
        detail_repository: ActivityDetailRepository,
    ) -> None:
        self.activity_repository = activity_repository
        self.detail_repository = detail_repository

    def get(
        self,
        athlete_profile_id: UUID,
        *,
        activity_id: UUID | None = None,
        activity_date: date | None = None,
        latest: bool = False,
        activity_name: str | None = None,
    ) -> ActivityDetailResult:
        """Sélectionne une activité sans jamais sortir du périmètre athlète."""
        selectors = sum((
            activity_id is not None,
            activity_date is not None,
            latest,
        ))
        if selectors != 1:
            raise ValueError(
                "Fournir exactement un sélecteur : activity_id, activity_date ou latest=true."
            )

        if activity_id is not None:
            activity = self.activity_repository.get_activity(
                athlete_profile_id,
                activity_id,
            )
            activities = [activity] if activity is not None else []
        elif latest:
            activities = self.activity_repository.list_activities(
                athlete_profile_id
            )[:1]
        else:
            activities = self.activity_repository.list_activities_between(
                athlete_profile_id,
                activity_date,
                activity_date,
            )

        if activity_name:
            needle = activity_name.casefold()
            activities = [
                item for item in activities
                if needle in item.name.casefold()
            ]

        if not activities:
            return ActivityDetailResult(
                status="not_found",
                selection_activity_id=activity_id,
                selection_date=activity_date,
            )

        if len(activities) > 1:
            return ActivityDetailResult(
                status="ambiguous",
                choices=tuple(activities[:10]),
                choices_truncated=len(activities) > 10,
                selection_activity_id=activity_id,
                selection_date=activity_date,
            )

        activity = activities[0]
        detail = self.detail_repository.get_activity_detail(
            athlete_profile_id,
            activity.id,
        )
        return ActivityDetailResult(
            status="ok",
            activity=activity,
            detail=detail,
            selection_activity_id=activity_id,
            selection_date=activity_date,
        )
