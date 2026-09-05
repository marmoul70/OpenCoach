from __future__ import annotations

from datetime import (
    date,
    datetime,
    timezone,
)
from uuid import UUID, uuid4

from opencoach.coaching.weekly_debrief_application import (
    WeeklyDebriefApplicationService,
    WeeklyDebriefPlanningContext,
)
from opencoach.coaching.weekly_debrief_orchestrator import (
    WeeklyDebriefOrchestrationBatch,
)
from opencoach.coaching.weekly_debrief_runtime_context import (
    WeeklyDebriefRuntimeFacts,
)


class FakeRuntime:
    def __init__(
        self,
        *,
        athlete_profile_ids: tuple[
            UUID,
            ...,
        ],
        facts: dict[
            UUID,
            WeeklyDebriefRuntimeFacts,
        ],
    ) -> None:
        self.athlete_profile_ids = (
            athlete_profile_ids
        )
        self.facts = facts

        self.calls: list[
            tuple[
                UUID,
                date,
            ]
        ] = []

    def active_profile_ids(
        self,
    ) -> tuple[UUID, ...]:
        return self.athlete_profile_ids

    def build_runtime_facts(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
    ) -> WeeklyDebriefRuntimeFacts:
        self.calls.append(
            (
                athlete_profile_id,
                reference_date,
            )
        )

        return self.facts[
            athlete_profile_id
        ]


class FakeOrchestrator:
    def __init__(
        self,
    ) -> None:
        self.contexts = ()

    def process_many(
        self,
        contexts,
    ) -> WeeklyDebriefOrchestrationBatch:
        self.contexts = tuple(
            contexts
        )

        return (
            WeeklyDebriefOrchestrationBatch(
                results=(),
            )
        )


class FakePlanningContextResolver:
    def __init__(
        self,
        context: WeeklyDebriefPlanningContext,
    ) -> None:
        self.context = context
        self.calls = []

    def resolve(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
        runtime_facts: WeeklyDebriefRuntimeFacts,
    ) -> WeeklyDebriefPlanningContext:
        self.calls.append(
            (
                athlete_profile_id,
                reference_date,
                runtime_facts,
            )
        )

        return self.context


def _facts(
    *,
    key_session_ids: frozenset[
        UUID
    ] = frozenset(),
) -> WeeklyDebriefRuntimeFacts:
    return WeeklyDebriefRuntimeFacts(
        week_start=date(
            2026,
            8,
            31,
        ),
        week_end=date(
            2026,
            9,
            6,
        ),
        has_remaining_planned_session=(
            False
        ),
        completed_sessions_count=1,
        last_completed_at=datetime(
            2026,
            9,
            6,
            18,
            10,
            tzinfo=timezone.utc,
        ),
        key_session_ids=(
            key_session_ids
        ),
    )


def test_application_builds_runtime_contexts() -> None:
    athlete_a = uuid4()
    athlete_b = uuid4()

    key_session_id = uuid4()

    runtime = FakeRuntime(
        athlete_profile_ids=(
            athlete_a,
            athlete_b,
        ),
        facts={
            athlete_a: _facts(
                key_session_ids=frozenset(
                    {
                        key_session_id,
                    }
                )
            ),
            athlete_b: _facts(),
        },
    )

    orchestrator = FakeOrchestrator()

    service = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
    )

    reference_date = date(
        2026,
        9,
        6,
    )

    now = datetime(
        2026,
        9,
        6,
        20,
        30,
        tzinfo=timezone.utc,
    )

    result = service.execute(
        reference_date=reference_date,
        now=now,
    )

    assert isinstance(
        result,
        WeeklyDebriefOrchestrationBatch,
    )

    assert runtime.calls == [
        (
            athlete_a,
            reference_date,
        ),
        (
            athlete_b,
            reference_date,
        ),
    ]

    assert len(
        orchestrator.contexts
    ) == 2

    first = orchestrator.contexts[0]

    assert (
        first.athlete_profile_id
        == athlete_a
    )

    assert first.week_start == date(
        2026,
        8,
        31,
    )

    assert first.week_end == date(
        2026,
        9,
        6,
    )

    assert first.now == now

    assert (
        first.has_remaining_planned_session
        is False
    )

    assert (
        first.key_session_ids
        == frozenset(
            {
                key_session_id,
            }
        )
    )

    assert first.planning_input is None
    assert (
        first.physiological_reference_date
        is None
    )
    assert first.sport_disciplines == ()
    assert first.reconcile_from_date is None
    assert first.additional_context == ()


def test_application_forwards_planning_context() -> None:
    athlete_profile_id = uuid4()

    runtime_facts = _facts()

    runtime = FakeRuntime(
        athlete_profile_ids=(
            athlete_profile_id,
        ),
        facts={
            athlete_profile_id: (
                runtime_facts
            ),
        },
    )

    orchestrator = FakeOrchestrator()

    planning_input = object()

    planning_context = (
        WeeklyDebriefPlanningContext(
            planning_input=planning_input,
            physiological_reference_date=(
                date(
                    2026,
                    9,
                    5,
                )
            ),
            sport_disciplines=(
                "Run",
                "TrailRun",
            ),
            reconcile_from_date=date(
                2026,
                9,
                7,
            ),
            additional_context=(
                "Conserver la progressivité.",
            ),
        )
    )

    resolver = (
        FakePlanningContextResolver(
            planning_context
        )
    )

    service = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
        planning_context_resolver=resolver,
    )

    reference_date = date(
        2026,
        9,
        6,
    )

    now = datetime(
        2026,
        9,
        6,
        21,
        0,
        tzinfo=timezone.utc,
    )

    service.execute(
        reference_date=reference_date,
        now=now,
    )

    assert len(
        resolver.calls
    ) == 1

    (
        resolved_profile_id,
        resolved_reference_date,
        resolved_runtime_facts,
    ) = resolver.calls[0]

    assert (
        resolved_profile_id
        == athlete_profile_id
    )

    assert (
        resolved_reference_date
        == reference_date
    )

    assert (
        resolved_runtime_facts
        is runtime_facts
    )

    context = (
        orchestrator.contexts[0]
    )

    assert (
        context.planning_input
        is planning_input
    )

    assert (
        context.physiological_reference_date
        == date(
            2026,
            9,
            5,
        )
    )

    assert (
        context.sport_disciplines
        == (
            "Run",
            "TrailRun",
        )
    )

    assert (
        context.reconcile_from_date
        == date(
            2026,
            9,
            7,
        )
    )

    assert (
        context.additional_context
        == (
            "Conserver la progressivité.",
        )
    )


def test_application_handles_no_active_profile() -> None:
    runtime = FakeRuntime(
        athlete_profile_ids=(),
        facts={},
    )

    orchestrator = FakeOrchestrator()

    service = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
    )

    result = service.execute(
        reference_date=date(
            2026,
            9,
            6,
        ),
        now=datetime(
            2026,
            9,
            6,
            21,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert runtime.calls == []
    assert orchestrator.contexts == ()

    assert result.results == ()
    assert result.completed == 0
    assert result.already_completed == 0
    assert result.waiting == 0
    assert result.failed == 0


def test_application_isolates_runtime_failure_between_profiles() -> None:
    """Un profil invalide ne doit pas bloquer les profils suivants."""

    athlete_a = uuid4()
    athlete_b = uuid4()
    athlete_c = uuid4()

    class SelectiveRuntime(FakeRuntime):
        def build_runtime_facts(
            self,
            *,
            athlete_profile_id: UUID,
            reference_date: date,
        ) -> WeeklyDebriefRuntimeFacts:
            self.calls.append(
                (
                    athlete_profile_id,
                    reference_date,
                )
            )

            if athlete_profile_id == athlete_b:
                raise RuntimeError(
                    "runtime failure for athlete B"
                )

            return self.facts[
                athlete_profile_id
            ]

    runtime = SelectiveRuntime(
        athlete_profile_ids=(
            athlete_a,
            athlete_b,
            athlete_c,
        ),
        facts={
            athlete_a: _facts(),
            athlete_c: _facts(),
        },
    )

    orchestrator = FakeOrchestrator()

    service = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
    )

    reference_date = date(
        2026,
        9,
        6,
    )

    now = datetime(
        2026,
        9,
        6,
        21,
        0,
        tzinfo=timezone.utc,
    )

    result = service.execute(
        reference_date=reference_date,
        now=now,
    )

    assert isinstance(
        result,
        WeeklyDebriefOrchestrationBatch,
    )

    assert runtime.calls == [
        (
            athlete_a,
            reference_date,
        ),
        (
            athlete_b,
            reference_date,
        ),
        (
            athlete_c,
            reference_date,
        ),
    ]

    processed_profile_ids = [
        context.athlete_profile_id
        for context in orchestrator.contexts
    ]

    assert processed_profile_ids == [
        athlete_a,
        athlete_c,
    ]


def test_application_returns_auditable_results_when_runtime_fails() -> None:
    """Le batch conserve A/B/C et marque uniquement B en échec."""

    from opencoach.coaching.weekly_debrief_eligibility import (
        WeeklyClosureEligibility,
    )
    from opencoach.coaching.weekly_debrief_orchestrator import (
        WeeklyDebriefOrchestrationResult,
        WeeklyDebriefOrchestrationStatus,
    )

    athlete_a = uuid4()
    athlete_b = uuid4()
    athlete_c = uuid4()

    class SelectiveRuntime(FakeRuntime):
        def build_runtime_facts(
            self,
            *,
            athlete_profile_id: UUID,
            reference_date: date,
        ) -> WeeklyDebriefRuntimeFacts:
            self.calls.append(
                (
                    athlete_profile_id,
                    reference_date,
                )
            )

            if athlete_profile_id == athlete_b:
                raise RuntimeError(
                    "runtime failure for athlete B"
                )

            return self.facts[
                athlete_profile_id
            ]

    class AuditableOrchestrator:
        def __init__(self) -> None:
            self.contexts = ()

        def process_many(
            self,
            contexts,
        ) -> WeeklyDebriefOrchestrationBatch:
            self.contexts = tuple(contexts)

            return WeeklyDebriefOrchestrationBatch(
                results=tuple(
                    WeeklyDebriefOrchestrationResult(
                        athlete_profile_id=(
                            context.athlete_profile_id
                        ),
                        status=(
                            WeeklyDebriefOrchestrationStatus.COMPLETED
                        ),
                        eligibility=(
                            WeeklyClosureEligibility.CLOSE
                        ),
                        reason="test completed",
                    )
                    for context in self.contexts
                )
            )

    runtime = SelectiveRuntime(
        athlete_profile_ids=(
            athlete_a,
            athlete_b,
            athlete_c,
        ),
        facts={
            athlete_a: _facts(),
            athlete_c: _facts(),
        },
    )

    orchestrator = AuditableOrchestrator()

    service = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
    )

    result = service.execute(
        reference_date=date(
            2026,
            9,
            6,
        ),
        now=datetime(
            2026,
            9,
            6,
            21,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert [
        context.athlete_profile_id
        for context in orchestrator.contexts
    ] == [
        athlete_a,
        athlete_c,
    ]

    assert [
        item.athlete_profile_id
        for item in result.results
    ] == [
        athlete_a,
        athlete_b,
        athlete_c,
    ]

    assert [
        item.status
        for item in result.results
    ] == [
        WeeklyDebriefOrchestrationStatus.COMPLETED,
        WeeklyDebriefOrchestrationStatus.FAILED,
        WeeklyDebriefOrchestrationStatus.COMPLETED,
    ]

    assert result.completed == 2
    assert result.failed == 1

    assert (
        "RuntimeError: runtime failure for athlete B"
        in (
            result.results[1].error
            or ""
        )
    )


def test_application_isolates_planning_context_failure() -> None:
    """Une erreur du resolver de B ne doit contaminer ni A ni C."""

    from opencoach.coaching.weekly_debrief_eligibility import (
        WeeklyClosureEligibility,
    )
    from opencoach.coaching.weekly_debrief_orchestrator import (
        WeeklyDebriefOrchestrationResult,
        WeeklyDebriefOrchestrationStatus,
    )

    athlete_a = uuid4()
    athlete_b = uuid4()
    athlete_c = uuid4()

    runtime = FakeRuntime(
        athlete_profile_ids=(
            athlete_a,
            athlete_b,
            athlete_c,
        ),
        facts={
            athlete_a: _facts(),
            athlete_b: _facts(),
            athlete_c: _facts(),
        },
    )

    planning_context = WeeklyDebriefPlanningContext(
        planning_input=object(),
        physiological_reference_date=date(
            2026,
            9,
            7,
        ),
        sport_disciplines=(
            "Run",
        ),
        reconcile_from_date=date(
            2026,
            9,
            7,
        ),
        additional_context=(),
    )

    class SelectiveResolver:
        def __init__(self) -> None:
            self.calls = []

        def resolve(
            self,
            *,
            athlete_profile_id: UUID,
            reference_date: date,
            runtime_facts: WeeklyDebriefRuntimeFacts,
        ) -> WeeklyDebriefPlanningContext:
            self.calls.append(
                athlete_profile_id
            )

            if athlete_profile_id == athlete_b:
                raise RuntimeError(
                    "resolver failure for athlete B"
                )

            return planning_context

    class AuditableOrchestrator:
        def __init__(self) -> None:
            self.contexts = ()

        def process_many(
            self,
            contexts,
        ) -> WeeklyDebriefOrchestrationBatch:
            self.contexts = tuple(contexts)

            return WeeklyDebriefOrchestrationBatch(
                results=tuple(
                    WeeklyDebriefOrchestrationResult(
                        athlete_profile_id=(
                            context.athlete_profile_id
                        ),
                        status=(
                            WeeklyDebriefOrchestrationStatus.COMPLETED
                        ),
                        eligibility=(
                            WeeklyClosureEligibility.CLOSE
                        ),
                        reason="test completed",
                    )
                    for context in self.contexts
                )
            )

    resolver = SelectiveResolver()
    orchestrator = AuditableOrchestrator()

    service = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
        planning_context_resolver=resolver,
    )

    result = service.execute(
        reference_date=date(
            2026,
            9,
            6,
        ),
        now=datetime(
            2026,
            9,
            6,
            21,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert resolver.calls == [
        athlete_a,
        athlete_b,
        athlete_c,
    ]

    assert [
        context.athlete_profile_id
        for context in orchestrator.contexts
    ] == [
        athlete_a,
        athlete_c,
    ]

    assert [
        item.athlete_profile_id
        for item in result.results
    ] == [
        athlete_a,
        athlete_b,
        athlete_c,
    ]

    assert [
        item.status
        for item in result.results
    ] == [
        WeeklyDebriefOrchestrationStatus.COMPLETED,
        WeeklyDebriefOrchestrationStatus.FAILED,
        WeeklyDebriefOrchestrationStatus.COMPLETED,
    ]

    assert result.completed == 2
    assert result.failed == 1

    assert (
        "RuntimeError: resolver failure for athlete B"
        in (
            result.results[1].error
            or ""
        )
    )



def test_application_does_not_resolve_planning_for_waiting_profile() -> None:
    """Un WAIT doit être décidé avant toute construction du planning."""
    from datetime import timedelta

    from opencoach.coaching.weekly_debrief_orchestrator import (
        WeeklyDebriefOrchestrator,
    )

    athlete_profile_id = uuid4()

    facts = WeeklyDebriefRuntimeFacts(
        week_start=date(
            2026,
            8,
            31,
        ),
        week_end=date(
            2026,
            9,
            6,
        ),
        has_remaining_planned_session=False,
        completed_sessions_count=1,
        last_completed_at=None,
        key_session_ids=frozenset(),
    )

    runtime = FakeRuntime(
        athlete_profile_ids=(
            athlete_profile_id,
        ),
        facts={
            athlete_profile_id: facts,
        },
    )

    class ForbiddenPlanningResolver:
        def __init__(self) -> None:
            self.calls = []

        def resolve(
            self,
            *,
            athlete_profile_id,
            reference_date,
            runtime_facts,
        ):
            self.calls.append(
                athlete_profile_id
            )

            raise AssertionError(
                "Le planning ne doit pas être résolu "
                "pour un profil WAIT."
            )

    class ForbiddenClosure:
        def execute(self, **kwargs):
            raise AssertionError(
                "La clôture ne doit pas être appelée."
            )

    class ForbiddenPlanningApplication:
        def execute(self, **kwargs):
            raise AssertionError(
                "Le planning ne doit pas être appliqué."
            )

    resolver = ForbiddenPlanningResolver()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=ForbiddenClosure(),
        planning_application_service=(
            ForbiddenPlanningApplication()
        ),
    )

    service = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
        planning_context_resolver=resolver,
    )

    result = service.execute(
        reference_date=date(
            2026,
            9,
            5,
        ),
        now=datetime(
            2026,
            9,
            5,
            18,
            30,
            tzinfo=timezone(
                timedelta(hours=2)
            ),
        ),
    )

    assert result.waiting == 1
    assert result.failed == 0
    assert resolver.calls == []


def test_application_resolves_planning_context_with_profile_factory() -> None:
    """Chaque athlète doit recevoir son propre resolver planning."""
    athlete_a = uuid4()
    athlete_b = uuid4()

    runtime = FakeRuntime(
        athlete_profile_ids=(
            athlete_a,
            athlete_b,
        ),
        facts={
            athlete_a: _facts(),
            athlete_b: _facts(),
        },
    )

    planning_a = WeeklyDebriefPlanningContext(
        planning_input=object(),
    )
    planning_b = WeeklyDebriefPlanningContext(
        planning_input=object(),
    )

    class Resolver:
        def __init__(
            self,
            *,
            expected_profile_id,
            planning_context,
        ) -> None:
            self.expected_profile_id = (
                expected_profile_id
            )
            self.planning_context = planning_context
            self.calls = []

        def resolve(
            self,
            *,
            athlete_profile_id,
            reference_date,
            runtime_facts,
        ):
            assert (
                athlete_profile_id
                == self.expected_profile_id
            )

            self.calls.append(
                athlete_profile_id
            )

            return self.planning_context

    resolver_a = Resolver(
        expected_profile_id=athlete_a,
        planning_context=planning_a,
    )
    resolver_b = Resolver(
        expected_profile_id=athlete_b,
        planning_context=planning_b,
    )

    factory_calls = []

    def planning_context_factory(
        athlete_profile_id,
    ):
        factory_calls.append(
            athlete_profile_id
        )

        if athlete_profile_id == athlete_a:
            return resolver_a

        if athlete_profile_id == athlete_b:
            return resolver_b

        raise AssertionError(
            "Profil inattendu."
        )

    class CapturingOrchestrator:
        def __init__(self) -> None:
            self.contexts = ()

        def process_many(
            self,
            contexts,
        ):
            from opencoach.coaching.weekly_debrief_orchestrator import (
                WeeklyDebriefOrchestrationBatch,
            )

            self.contexts = tuple(contexts)

            return WeeklyDebriefOrchestrationBatch(
                results=()
            )

    orchestrator = CapturingOrchestrator()

    service = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
        planning_context_factory=(
            planning_context_factory
        ),
    )

    service.execute(
        reference_date=date(
            2026,
            9,
            6,
        ),
        now=datetime(
            2026,
            9,
            6,
            21,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert factory_calls == [
        athlete_a,
        athlete_b,
    ]

    assert resolver_a.calls == [
        athlete_a,
    ]

    assert resolver_b.calls == [
        athlete_b,
    ]

    contexts_by_profile = {
        context.athlete_profile_id: context
        for context in orchestrator.contexts
    }

    assert (
        contexts_by_profile[
            athlete_a
        ].planning_input
        is planning_a.planning_input
    )

    assert (
        contexts_by_profile[
            athlete_b
        ].planning_input
        is planning_b.planning_input
    )


def test_application_does_not_resolve_planning_for_no_debrief() -> None:
    from opencoach.coaching.weekly_debrief_eligibility import (
        WeeklyClosureEligibility,
    )
    from opencoach.coaching.weekly_debrief_orchestrator import (
        WeeklyDebriefOrchestrationBatch,
        WeeklyDebriefOrchestrationResult,
        WeeklyDebriefOrchestrationStatus,
    )

    athlete_profile_id = uuid4()

    runtime = FakeRuntime(
        athlete_profile_ids=(
            athlete_profile_id,
        ),
        facts={
            athlete_profile_id: WeeklyDebriefRuntimeFacts(
                week_start=date(
                    2026,
                    8,
                    31,
                ),
                week_end=date(
                    2026,
                    9,
                    6,
                ),
                has_remaining_planned_session=False,
                completed_sessions_count=0,
                last_completed_at=None,
                key_session_ids=frozenset(),
            ),
        },
    )

    class FailingResolver:
        def resolve(
            self,
            **kwargs,
        ):
            del kwargs

            raise AssertionError(
                "Le resolver planning ne doit pas être "
                "appelé pour un profil sans séance réalisée."
            )

    class CapturingOrchestrator:
        def __init__(self) -> None:
            self.contexts = ()

        def process_many(
            self,
            contexts,
        ):
            self.contexts = tuple(
                contexts
            )

            return WeeklyDebriefOrchestrationBatch(
                results=tuple(
                    WeeklyDebriefOrchestrationResult(
                        athlete_profile_id=(
                            context.athlete_profile_id
                        ),
                        status=(
                            WeeklyDebriefOrchestrationStatus.NO_DEBRIEF
                        ),
                        eligibility=(
                            WeeklyClosureEligibility.CLOSE
                        ),
                        reason="Aucun débrief.",
                    )
                    for context in self.contexts
                )
            )

    orchestrator = CapturingOrchestrator()

    application = WeeklyDebriefApplicationService(
        runtime=runtime,
        orchestrator=orchestrator,
        planning_context_resolver=FailingResolver(),
    )

    result = application.execute(
        reference_date=date(
            2026,
            9,
            6,
        ),
        now=datetime(
            2026,
            9,
            6,
            20,
            30,
            tzinfo=timezone.utc,
        ),
    )

    assert len(
        orchestrator.contexts
    ) == 1

    profile_context = (
        orchestrator.contexts[0]
    )

    assert (
        profile_context.completed_sessions_count
        == 0
    )

    assert (
        profile_context.planning_input
        is None
    )

    assert result.no_debrief == 1
    assert result.failed == 0
