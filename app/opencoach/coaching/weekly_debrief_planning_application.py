"""Application d'une adaptation hebdomadaire persistée.

Ce module reprend une décision issue d'un débrief déjà fermé,
l'applique au moteur de génération existant puis marque l'étape
planning comme terminée.

Il ne recalcule jamais le débrief et n'envoie aucune notification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from types import UnionType
from typing import (
    Any,
    Callable,
    Protocol,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from uuid import UUID

from opencoach.coaching.weekly_adaptation import (
    WeeklyAdaptationDecision,
)
from opencoach.database.repositories.weekly_debrief import (
    StoredWeeklyDebrief,
)


class WeeklyDebriefNotClosedError(RuntimeError):
    """Aucun débrief fermé n'existe pour la semaine."""


class WeeklyAdaptationPayloadError(RuntimeError):
    """Le payload d'adaptation fermé est absent ou invalide."""


class WeeklyPlanningApplicationError(RuntimeError):
    """L'application de l'adaptation n'a pas pu être finalisée."""


class WeeklyDebriefPlanningRepository(Protocol):
    """Port minimal de reprise de l'orchestration hebdomadaire."""

    def get_for_week(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> StoredWeeklyDebrief | None:
        ...

    def mark_planning_updated(
        self,
        athlete_profile_id: UUID,
        week_start: date,
        *,
        timestamp=None,
    ) -> StoredWeeklyDebrief | None:
        ...


class WeeklyWorkoutSyncService(Protocol):
    """Port optionnel de synchronisation du planning externe."""

    def sync_period(
        self,
        *,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> object:
        ...



class WeeklyPlanningGenerator(Protocol):
    """Port du moteur de génération hebdomadaire existant."""

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        planning_input: object,
        physiological_reference_date=None,
        sport_disciplines=(),
        weekly_adaptation=None,
        reconcile_from_date=None,
        additional_context=(),
    ) -> object:
        ...


@dataclass(frozen=True, slots=True)
class WeeklyPlanningApplicationResult:
    """Résultat de l'étape d'application au planning."""

    stored_debrief: StoredWeeklyDebrief
    planning_result: object | None
    already_applied: bool


def _coerce_value(
    annotation: Any,
    value: Any,
) -> Any:
    """Reconstruit une valeur depuis son équivalent JSON."""

    if value is None:
        return None

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in {
        Union,
        UnionType,
    }:
        non_none = tuple(
            item
            for item in args
            if item is not type(None)
        )

        if len(non_none) == 1:
            return _coerce_value(
                non_none[0],
                value,
            )

    try:
        if (
            isinstance(annotation, type)
            and issubclass(annotation, Enum)
        ):
            return annotation(value)
    except TypeError:
        pass

    if origin is tuple:
        item_type = (
            args[0]
            if args
            else Any
        )

        return tuple(
            _coerce_value(
                item_type,
                item,
            )
            for item in value
        )

    if origin is list:
        item_type = (
            args[0]
            if args
            else Any
        )

        return [
            _coerce_value(
                item_type,
                item,
            )
            for item in value
        ]

    if origin is frozenset:
        item_type = (
            args[0]
            if args
            else Any
        )

        return frozenset(
            _coerce_value(
                item_type,
                item,
            )
            for item in value
        )

    return value


def deserialize_weekly_adaptation_decision(
    payload: dict,
) -> WeeklyAdaptationDecision:
    """Reconstruit la décision métier persistée par T6.5.3."""

    if not isinstance(payload, dict):
        raise WeeklyAdaptationPayloadError(
            "Le payload d'adaptation n'est pas un objet JSON."
        )

    hints = get_type_hints(
        WeeklyAdaptationDecision
    )

    required = tuple(
        WeeklyAdaptationDecision.__dataclass_fields__
    )

    missing = [
        name
        for name in required
        if name not in payload
    ]

    if missing:
        raise WeeklyAdaptationPayloadError(
            "Payload d'adaptation incomplet : "
            + ", ".join(sorted(missing))
        )

    unexpected = (
        set(payload)
        - set(required)
    )

    if unexpected:
        raise WeeklyAdaptationPayloadError(
            "Payload d'adaptation contient des champs inconnus : "
            + ", ".join(sorted(unexpected))
        )

    try:
        kwargs = {
            name: _coerce_value(
                hints.get(name, Any),
                payload[name],
            )
            for name in required
        }

        return WeeklyAdaptationDecision(
            **kwargs
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise WeeklyAdaptationPayloadError(
            "Impossible de reconstruire "
            "WeeklyAdaptationDecision."
        ) from exc


class WeeklyDebriefPlanningApplicationService:
    """Applique au planning la décision d'un débrief fermé."""

    def __init__(
        self,
        *,
        debrief_repository: WeeklyDebriefPlanningRepository,
        planning_service: (
            WeeklyPlanningGenerator | None
        ) = None,
        planning_service_factory: (
            Callable[
                [UUID],
                WeeklyPlanningGenerator,
            ]
            | None
        ) = None,
        workout_sync_service: (
            WeeklyWorkoutSyncService | None
        ) = None,
    ) -> None:
        if (
            planning_service is None
            and planning_service_factory is None
        ):
            raise ValueError(
                "Un planning_service ou une "
                "planning_service_factory est requis."
            )

        self._debrief_repository = debrief_repository
        self._planning_service = planning_service
        self._planning_service_factory = (
            planning_service_factory
        )
        self._workout_sync_service = (
            workout_sync_service
        )

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        closed_week_start: date,
        planning_input: object,
        physiological_reference_date=None,
        sport_disciplines=(),
        reconcile_from_date=None,
        additional_context=(),
    ) -> WeeklyPlanningApplicationResult:
        """Applique exactement une fois l'adaptation persistée."""

        stored = (
            self._debrief_repository.get_for_week(
                athlete_profile_id,
                closed_week_start,
            )
        )

        if stored is None:
            raise WeeklyDebriefNotClosedError(
                "Aucun débrief hebdomadaire fermé "
                "n'existe pour cette semaine."
            )

        if stored.planning_updated_at is not None:
            return WeeklyPlanningApplicationResult(
                stored_debrief=stored,
                planning_result=None,
                already_applied=True,
            )

        payload = stored.adaptation_payload

        if payload is None:
            raise WeeklyAdaptationPayloadError(
                "Le débrief fermé ne contient "
                "aucune décision d'adaptation."
            )

        decision = (
            deserialize_weekly_adaptation_decision(
                payload
            )
        )

        planning_service = self._planning_service

        if self._planning_service_factory is not None:
            planning_service = (
                self._planning_service_factory(
                    athlete_profile_id
                )
            )

        if planning_service is None:
            raise WeeklyPlanningApplicationError(
                "Aucun service de planification "
                "n'est disponible pour cet athlète."
            )

        planning_result = (
            planning_service.execute(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                planning_input=planning_input,
                physiological_reference_date=(
                    physiological_reference_date
                ),
                sport_disciplines=(
                    sport_disciplines
                ),
                weekly_adaptation=decision,
                reconcile_from_date=(
                    reconcile_from_date
                ),
                additional_context=(
                    additional_context
                ),
            )
        )

        updated = (
            self._debrief_repository
            .mark_planning_updated(
                athlete_profile_id,
                closed_week_start,
            )
        )

        if updated is None:
            raise WeeklyPlanningApplicationError(
                "Le planning a été généré mais "
                "planning_updated_at n'a pas pu être persisté."
            )

        self._sync_next_week_best_effort(
            athlete_profile_id=athlete_profile_id,
            closed_week_start=closed_week_start,
        )

        return WeeklyPlanningApplicationResult(
            stored_debrief=updated,
            planning_result=planning_result,
            already_applied=False,
        )


    def _sync_next_week_best_effort(
        self,
        *,
        athlete_profile_id: UUID,
        closed_week_start: date,
    ) -> None:
        """Synchronise N+1 sans invalider le planning OpenCoach."""

        service = self._workout_sync_service

        if service is None:
            return

        from datetime import timedelta

        next_week_start = (
            closed_week_start
            + timedelta(days=7)
        )
        next_week_end = (
            next_week_start
            + timedelta(days=6)
        )

        try:
            service.sync_period(
                athlete_profile_id=athlete_profile_id,
                start_date=next_week_start,
                end_date=next_week_end,
            )
        except Exception:
            # La synchronisation Intervals est un effet externe.
            # Une panne distante ne doit jamais invalider le
            # débrief ni le planning déjà persisté.
            return
