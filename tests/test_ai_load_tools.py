from uuid import uuid4

from opencoach.ai.load_tools import (
    TrainingLoadArguments,
    build_training_load_tool,
)


def test_training_load_tool_delegates_complete_analysis_to_coach_service():
    athlete_id = uuid4()
    expected = {
        "status": "ok",
        "period": {"start_date": "2026-11-08", "end_date": "2026-11-08"},
        "load": {"actual_total": 42.0},
    }
    calls = []

    class FakeRecentLoadService:
        def analysis_summary(self, profile_id, *, days=None):
            calls.append((profile_id, days))
            return expected

    tool = build_training_load_tool(FakeRecentLoadService(), athlete_id)

    assert tool.handler(TrainingLoadArguments(nb_days=1)) is expected
    assert calls == [(athlete_id, 1)]


def test_training_load_tool_leaves_default_window_to_coach_service():
    athlete_id = uuid4()
    calls = []

    class FakeRecentLoadService:
        def analysis_summary(self, profile_id, *, days=None):
            calls.append((profile_id, days))
            return {"status": "ok", "period": {"nb_days": 7}}

    tool = build_training_load_tool(FakeRecentLoadService(), athlete_id)

    assert tool.handler(TrainingLoadArguments()) == {
        "status": "ok",
        "period": {"nb_days": 7},
    }
    assert calls == [(athlete_id, None)]


def test_training_load_argument_schema_does_not_own_period_limits():
    assert TrainingLoadArguments(nb_days=0).nb_days == 0
    assert TrainingLoadArguments(nb_days=91).nb_days == 91
    assert TrainingLoadArguments().nb_days is None


def test_training_load_adapter_does_not_compose_domain_services():
    import inspect

    source = inspect.getsource(build_training_load_tool)
    assert "calculate_days" not in source
    assert ".calculate(" not in source
    assert "analysis_summary(" in source
