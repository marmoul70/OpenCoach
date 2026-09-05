"""Clôture applicative du débrief hebdomadaire.

Ce service orchestre uniquement la construction et la persistance
du bilan fermé d'une semaine.

Il ne modifie pas le planning suivant, n'envoie aucune notification
et ne décide pas du moment où la clôture doit être déclenchée.
Ces responsabilités appartiennent aux étapes d'orchestration
suivantes.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date
from enum import Enum
from typing import Any, Protocol
from uuid import UUID

from opencoach.coaching.weekly_adaptation import (
    build_weekly_adaptation_decision,
)
from opencoach.coaching.weekly_debrief import (
    build_weekly_debrief,
)
from opencoach.coaching.weekly_debrief_facts import (
    WeeklyActivityReader,
    WeeklyTrainingSessionReader,
    build_weekly_debrief_facts_from_history,
)
from opencoach.database.repositories.weekly_debrief import (
    StoredWeeklyDebrief,
    WeeklyDebriefRepository,
)


class WeeklyPlanReader(Protocol):
    """Lecture du plan hebdomadaire persistant."""

    def get_plan_for_week(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> object | None:
        ...


class SessionExecutionAnalysisReader(Protocol):
    """Lecture du débriefing persisté d'une séance."""

    def get_for_session(
        self,
        *,
        athlete_profile_id: UUID,
        training_session_id: UUID,
    ) -> object | None:
        ...


def _json_value(value: Any) -> Any:
    """Convertit récursivement un objet métier en valeur JSON."""

    if isinstance(value, Enum):
        return value.value

    if is_dataclass(value):
        return _json_value(
            asdict(value)
        )

    if isinstance(value, dict):
        return {
            str(key): _json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (tuple, list, set, frozenset)):
        return [
            _json_value(item)
            for item in value
        ]

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, date):
        return value.isoformat()

    return value


def serialize_weekly_adaptation_decision(
    decision: object,
) -> dict:
    """Sérialise la décision d'adaptation pour la persistance."""

    payload = _json_value(decision)

    if not isinstance(payload, dict):
        raise TypeError(
            "La décision d'adaptation doit être "
            "sérialisable sous forme d'objet JSON."
        )

    return payload


class WeeklyDebriefClosureService:
    """Construit et ferme le bilan d'une semaine terminée."""

    def __init__(
        self,
        *,
        session_reader: WeeklyTrainingSessionReader,
        activity_reader: WeeklyActivityReader,
        weekly_plan_reader: WeeklyPlanReader,
        execution_analysis_reader: (
            SessionExecutionAnalysisReader
        ),
        debrief_repository: WeeklyDebriefRepository,
    ) -> None:
        self._session_reader = session_reader
        self._activity_reader = activity_reader
        self._weekly_plan_reader = weekly_plan_reader
        self._execution_analysis_reader = (
            execution_analysis_reader
        )
        self._debrief_repository = debrief_repository

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        week_start: date,
        week_end: date,
        key_session_ids: frozenset[UUID] = frozenset(),
    ) -> StoredWeeklyDebrief:
        """Ferme le bilan ou retourne le snapshot déjà fermé.

        L'idempotence est vérifiée avant toute lecture coûteuse de
        l'historique de la semaine.
        """

        if week_end < week_start:
            raise ValueError(
                "week_end doit être postérieur ou égal "
                "à week_start."
            )

        existing = self._debrief_repository.get_for_week(
            athlete_profile_id,
            week_start,
        )

        if existing is not None:
            return existing

        sessions = list(
            self._session_reader.list_sessions_between(
                athlete_profile_id,
                week_start,
                week_end,
            )
        )

        weekly_plan = (
            self._weekly_plan_reader.get_plan_for_week(
                athlete_profile_id,
                week_start,
            )
        )

        completed_session_ids = tuple(
            session.id
            for session in sessions
            if (
                session.status == "completed"
                and getattr(session, "id", None)
                is not None
            )
        )

        execution_analyses = {}

        for session_id in completed_session_ids:
            analysis = (
                self._execution_analysis_reader
                .get_for_session(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    training_session_id=session_id,
                )
            )

            if analysis is not None:
                execution_analyses[
                    session_id
                ] = analysis

        # Le builder T6.5.2 possède sa propre lecture des séances.
        # Afin de garantir qu'une seule photographie soit utilisée
        # pendant toute la clôture, on lui fournit une vue figée.
        frozen_session_reader = (
            _FrozenSessionReader(sessions)
        )

        facts = (
            build_weekly_debrief_facts_from_history(
                athlete_profile_id=athlete_profile_id,
                week_start=week_start,
                week_end=week_end,
                session_reader=frozen_session_reader,
                activity_reader=self._activity_reader,
                weekly_plan=weekly_plan,
                execution_analyses=execution_analyses,
                key_session_ids=key_session_ids,
            )
        )

        debrief = build_weekly_debrief(
            facts
        )

        adaptation = (
            build_weekly_adaptation_decision(
                debrief
            )
        )

        adaptation_payload = (
            serialize_weekly_adaptation_decision(
                adaptation
            )
        )

        return self._debrief_repository.save_closed(
            athlete_profile_id,
            facts,
            debrief,
            adaptation_payload=adaptation_payload,
        )


class _FrozenSessionReader:
    """Vue immutable des séances déjà lues par le service."""

    def __init__(
        self,
        sessions: list,
    ) -> None:
        self._sessions = tuple(
            sessions
        )

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list:
        del athlete_profile_id
        del start_date
        del end_date

        return list(
            self._sessions
        )
