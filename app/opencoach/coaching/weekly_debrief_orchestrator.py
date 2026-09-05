"""Orchestration hebdomadaire du débrief OpenCoach.

Cette couche assemble :

- l'éligibilité temporelle T6.5.5 ;
- la clôture immuable T6.5.3 ;
- l'application au planning T6.5.4.

Elle reste indépendante du scheduler, de SQLAlchemy et du push.

Une erreur concernant un athlète ne doit jamais interrompre le
traitement des autres athlètes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Iterable
from uuid import UUID

from opencoach.coaching.weekly_debrief_eligibility import (
    WeeklyClosureEligibility,
    evaluate_weekly_closure_eligibility,
)


class WeeklyDebriefOrchestrationStatus(StrEnum):
    """État final d'un passage d'orchestration."""

    WAIT = "wait"
    COMPLETED = "completed"
    ALREADY_COMPLETED = "already_completed"
    NO_DEBRIEF = "no_debrief"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WeeklyDebriefProfileContext:
    """Contexte déjà résolu pour un athlète."""

    athlete_profile_id: UUID

    week_start: date
    week_end: date

    now: datetime

    has_remaining_planned_session: bool

    completed_sessions_count: int

    last_completed_at: datetime | None = None

    planning_input: object | None = None

    key_session_ids: frozenset[UUID] = frozenset()

    physiological_reference_date: date | None = None

    sport_disciplines: tuple = ()

    reconcile_from_date: date | None = None

    additional_context: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WeeklyDebriefOrchestrationResult:
    """Résultat isolé d'un athlète."""

    athlete_profile_id: UUID

    status: WeeklyDebriefOrchestrationStatus

    eligibility: WeeklyClosureEligibility

    reason: str

    error: str | None = None


@dataclass(frozen=True, slots=True)
class WeeklyDebriefOrchestrationBatch:
    """Résultat global d'un passage multi-athlètes."""

    results: tuple[
        WeeklyDebriefOrchestrationResult,
        ...
    ]

    @property
    def completed(self) -> int:
        return sum(
            result.status
            is WeeklyDebriefOrchestrationStatus.COMPLETED
            for result in self.results
        )

    @property
    def already_completed(self) -> int:
        return sum(
            result.status
            is WeeklyDebriefOrchestrationStatus.ALREADY_COMPLETED
            for result in self.results
        )

    @property
    def waiting(self) -> int:
        return sum(
            result.status
            is WeeklyDebriefOrchestrationStatus.WAIT
            for result in self.results
        )

    @property
    def no_debrief(self) -> int:
        return sum(
            result.status
            is WeeklyDebriefOrchestrationStatus.NO_DEBRIEF
            for result in self.results
        )

    @property
    def failed(self) -> int:
        return sum(
            result.status
            is WeeklyDebriefOrchestrationStatus.FAILED
            for result in self.results
        )


class WeeklyDebriefOrchestrator:
    """Assemble les étapes persistantes du dimanche."""

    def __init__(
        self,
        *,
        closure_service,
        planning_application_service,
    ) -> None:
        self._closure_service = closure_service
        self._planning_application_service = (
            planning_application_service
        )

    def process_profile(
        self,
        context: WeeklyDebriefProfileContext,
    ) -> WeeklyDebriefOrchestrationResult:
        """Traite un athlète sans masquer les règles métier."""

        eligibility = (
            evaluate_weekly_closure_eligibility(
                now=context.now,
                week_end=context.week_end,
                has_remaining_planned_session=(
                    context.has_remaining_planned_session
                ),
                last_completed_at=(
                    context.last_completed_at
                ),
            )
        )

        if (
            eligibility.decision
            is WeeklyClosureEligibility.WAIT
        ):
            return WeeklyDebriefOrchestrationResult(
                athlete_profile_id=(
                    context.athlete_profile_id
                ),
                status=(
                    WeeklyDebriefOrchestrationStatus.WAIT
                ),
                eligibility=eligibility.decision,
                reason=eligibility.reason,
            )

        if context.completed_sessions_count == 0:
            return WeeklyDebriefOrchestrationResult(
                athlete_profile_id=(
                    context.athlete_profile_id
                ),
                status=(
                    WeeklyDebriefOrchestrationStatus.NO_DEBRIEF
                ),
                eligibility=eligibility.decision,
                reason=(
                    "Aucune séance réalisée cette semaine ; "
                    "aucun débrief hebdomadaire n'est généré."
                ),
            )

        if context.planning_input is None:
            return WeeklyDebriefOrchestrationResult(
                athlete_profile_id=(
                    context.athlete_profile_id
                ),
                status=(
                    WeeklyDebriefOrchestrationStatus.FAILED
                ),
                eligibility=eligibility.decision,
                reason=(
                    "La clôture est éligible mais le contexte "
                    "du planning suivant est indisponible."
                ),
                error="missing_planning_input",
            )

        try:
            self._closure_service.execute(
                athlete_profile_id=(
                    context.athlete_profile_id
                ),
                week_start=context.week_start,
                week_end=context.week_end,
                key_session_ids=(
                    context.key_session_ids
                ),
            )

            planning_result = (
                self._planning_application_service.execute(
                    athlete_profile_id=(
                        context.athlete_profile_id
                    ),
                    closed_week_start=(
                        context.week_start
                    ),
                    planning_input=(
                        context.planning_input
                    ),
                    physiological_reference_date=(
                        context.physiological_reference_date
                    ),
                    sport_disciplines=(
                        context.sport_disciplines
                    ),
                    reconcile_from_date=(
                        context.reconcile_from_date
                    ),
                    additional_context=(
                        context.additional_context
                    ),
                )
            )

        except Exception as exc:
            return WeeklyDebriefOrchestrationResult(
                athlete_profile_id=(
                    context.athlete_profile_id
                ),
                status=(
                    WeeklyDebriefOrchestrationStatus.FAILED
                ),
                eligibility=eligibility.decision,
                reason=(
                    "Une étape persistante du débrief "
                    "hebdomadaire a échoué."
                ),
                error=(
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        status = (
            WeeklyDebriefOrchestrationStatus.ALREADY_COMPLETED
            if planning_result.already_applied
            else WeeklyDebriefOrchestrationStatus.COMPLETED
        )

        return WeeklyDebriefOrchestrationResult(
            athlete_profile_id=(
                context.athlete_profile_id
            ),
            status=status,
            eligibility=eligibility.decision,
            reason=eligibility.reason,
        )

    def process_many(
        self,
        contexts: Iterable[
            WeeklyDebriefProfileContext
        ],
    ) -> WeeklyDebriefOrchestrationBatch:
        """Traite tous les athlètes indépendamment."""

        results = tuple(
            self._process_profile_safely(context)
            for context in contexts
        )

        return WeeklyDebriefOrchestrationBatch(
            results=results
        )

    def _process_profile_safely(
        self,
        context: WeeklyDebriefProfileContext,
    ) -> WeeklyDebriefOrchestrationResult:
        """Isole même une erreur d'éligibilité malformée."""

        try:
            return self.process_profile(
                context
            )

        except Exception as exc:
            return WeeklyDebriefOrchestrationResult(
                athlete_profile_id=(
                    context.athlete_profile_id
                ),
                status=(
                    WeeklyDebriefOrchestrationStatus.FAILED
                ),
                eligibility=(
                    WeeklyClosureEligibility.WAIT
                ),
                reason=(
                    "Le contexte de l'athlète "
                    "n'a pas pu être évalué."
                ),
                error=(
                    f"{type(exc).__name__}: {exc}"
                ),
            )
