"""Bridge applicatif du débrief hebdomadaire OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Protocol
from uuid import UUID

from opencoach.coaching.weekly_debrief_eligibility import (
    WeeklyClosureEligibility,
    evaluate_weekly_closure_eligibility,
)
from opencoach.coaching.weekly_debrief_orchestrator import (
    WeeklyDebriefOrchestrationBatch,
    WeeklyDebriefOrchestrator,
    WeeklyDebriefProfileContext,
)
from opencoach.coaching.weekly_debrief_runtime_context import (
    WeeklyDebriefRuntimeFacts,
)


class WeeklyDebriefApplicationRuntime(
    Protocol,
):
    """Runtime minimal requis par le bridge applicatif."""

    def active_profile_ids(
        self,
    ) -> tuple[UUID, ...]:
        """Retourne les profils athlètes à traiter."""

    def build_runtime_facts(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
    ) -> WeeklyDebriefRuntimeFacts:
        """Résout les faits runtime nécessaires au débrief."""


@dataclass(
    frozen=True,
    slots=True,
)
class WeeklyDebriefPlanningContext:
    """Contexte optionnel transmis à la planification suivante."""

    planning_input: object | None = None

    physiological_reference_date: (
        date | None
    ) = None

    sport_disciplines: tuple = ()

    reconcile_from_date: (
        date | None
    ) = None

    additional_context: tuple[
        str,
        ...,
    ] = ()


class WeeklyDebriefPlanningContextResolver(
    Protocol,
):
    """Résout l'enrichissement de planification d'un athlète."""

    def resolve(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
        runtime_facts: WeeklyDebriefRuntimeFacts,
    ) -> WeeklyDebriefPlanningContext:
        """Construit le contexte de planification à transmettre."""


class WeeklyDebriefApplicationService:
    """Relie le runtime SQL au moteur d'orchestration hebdomadaire."""

    def __init__(
        self,
        *,
        runtime: WeeklyDebriefApplicationRuntime,
        orchestrator: WeeklyDebriefOrchestrator,
        planning_context_resolver: (
            WeeklyDebriefPlanningContextResolver
            | None
        ) = None,
        planning_context_factory: (
            Callable[
                [UUID],
                WeeklyDebriefPlanningContextResolver,
            ]
            | None
        ) = None,
    ) -> None:
        self._runtime = runtime
        self._orchestrator = orchestrator
        self._planning_context_resolver = (
            planning_context_resolver
        )
        self._planning_context_factory = (
            planning_context_factory
        )

    def execute(
        self,
        *,
        reference_date: date,
        now: datetime,
    ) -> WeeklyDebriefOrchestrationBatch:
        """Traite tous les profils actifs indépendamment."""

        from opencoach.coaching.weekly_debrief_eligibility import (
            WeeklyClosureEligibility,
        )
        from opencoach.coaching.weekly_debrief_orchestrator import (
            WeeklyDebriefOrchestrationResult,
            WeeklyDebriefOrchestrationStatus,
        )

        valid_contexts = []
        context_failures = {}

        for athlete_profile_id in (
            self._runtime.active_profile_ids()
        ):
            try:
                context = self._build_profile_context(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    reference_date=reference_date,
                    now=now,
                )

            except Exception as exc:
                context_failures[
                    athlete_profile_id
                ] = WeeklyDebriefOrchestrationResult(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    status=(
                        WeeklyDebriefOrchestrationStatus.FAILED
                    ),
                    eligibility=(
                        WeeklyClosureEligibility.WAIT
                    ),
                    reason=(
                        "Le contexte hebdomadaire de "
                        "l'athlète n'a pas pu être construit."
                    ),
                    error=(
                        f"{type(exc).__name__}: {exc}"
                    ),
                )
                continue

            valid_contexts.append(context)

        processed = self._orchestrator.process_many(
            tuple(valid_contexts)
        )

        if not context_failures:
            return processed

        processed_by_profile = {
            result.athlete_profile_id: result
            for result in processed.results
        }

        results = []

        for athlete_profile_id in (
            self._runtime.active_profile_ids()
        ):
            failure = context_failures.get(
                athlete_profile_id
            )

            if failure is not None:
                results.append(failure)
                continue

            processed_result = (
                processed_by_profile.get(
                    athlete_profile_id
                )
            )

            if processed_result is not None:
                results.append(
                    processed_result
                )

        return WeeklyDebriefOrchestrationBatch(
            results=tuple(results)
        )

    def _build_profile_context(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
        now: datetime,
    ) -> WeeklyDebriefProfileContext:
        runtime_facts = (
            self._runtime.build_runtime_facts(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                reference_date=reference_date,
            )
        )

        eligibility = evaluate_weekly_closure_eligibility(
            now=now,
            week_end=runtime_facts.week_end,
            has_remaining_planned_session=(
                runtime_facts.has_remaining_planned_session
            ),
            last_completed_at=(
                runtime_facts.last_completed_at
            ),
        )

        if (
            eligibility.decision
            is WeeklyClosureEligibility.WAIT
            or runtime_facts.completed_sessions_count == 0
        ):
            planning_context = WeeklyDebriefPlanningContext()
        else:
            planning_context = (
                self._resolve_planning_context(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    reference_date=reference_date,
                    runtime_facts=runtime_facts,
                )
            )

        return WeeklyDebriefProfileContext(
            athlete_profile_id=(
                athlete_profile_id
            ),
            week_start=(
                runtime_facts.week_start
            ),
            week_end=(
                runtime_facts.week_end
            ),
            now=now,
            has_remaining_planned_session=(
                runtime_facts
                .has_remaining_planned_session
            ),
            completed_sessions_count=(
                runtime_facts.completed_sessions_count
            ),
            last_completed_at=(
                runtime_facts.last_completed_at
            ),
            planning_input=(
                planning_context.planning_input
            ),
            key_session_ids=(
                runtime_facts.key_session_ids
            ),
            physiological_reference_date=(
                planning_context
                .physiological_reference_date
            ),
            sport_disciplines=(
                planning_context
                .sport_disciplines
            ),
            reconcile_from_date=(
                planning_context
                .reconcile_from_date
            ),
            additional_context=(
                planning_context
                .additional_context
            ),
        )

    def _resolve_planning_context(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
        runtime_facts: WeeklyDebriefRuntimeFacts,
    ) -> WeeklyDebriefPlanningContext:
        planning_context_resolver = (
            self._planning_context_resolver
        )

        if self._planning_context_factory is not None:
            planning_context_resolver = (
                self._planning_context_factory(
                    athlete_profile_id
                )
            )

        if planning_context_resolver is None:
            return (
                WeeklyDebriefPlanningContext()
            )

        return (
            planning_context_resolver.resolve(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                reference_date=(
                    reference_date
                ),
                runtime_facts=runtime_facts,
            )
        )
