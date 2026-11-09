from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool, AIToolRegistry
from opencoach.ai.training_tools import build_training_history_tool


class EchoArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: int = Field(ge=1, le=5)


def test_registry_executes_only_registered_tool_and_returns_normalized_result():
    registry = AIToolRegistry()
    registry.register(
        AITool(
            name="echo",
            description="Outil de test.",
            arguments_model=EchoArguments,
            handler=lambda args: {"value": args.value},
        )
    )

    result = registry.execute("echo", {"value": 3})

    assert result.status == "ok"
    assert result.data == {"value": 3}
    assert result.metadata["executed_at"]
    assert registry.definitions()[0]["name"] == "echo"


def test_registry_rejects_unknown_tool_and_invalid_arguments():
    registry = AIToolRegistry()
    registry.register(
        AITool(
            name="echo",
            description="Outil de test.",
            arguments_model=EchoArguments,
            handler=lambda args: {"value": args.value},
        )
    )

    unknown = registry.execute("not_allowed", {})
    invalid = registry.execute("echo", {"value": 99, "unexpected": True})

    assert unknown.status == "not_found"
    assert invalid.status == "invalid_arguments"


def test_registry_does_not_expose_internal_exception_details():
    registry = AIToolRegistry()

    def fail(_args):
        raise RuntimeError("database password must not leak")

    registry.register(
        AITool(
            name="failure",
            description="Outil de test.",
            arguments_model=EchoArguments,
            handler=fail,
        )
    )

    result = registry.execute("failure", {"value": 1})

    assert result.status == "failed"
    assert "password" not in (result.error or "")


def test_training_history_tool_uses_injected_athlete_and_inclusive_period():
    athlete_id = uuid4()
    calls = []

    def calculate(profile_id, start_date, end_date):
        calls.append((profile_id, start_date, end_date))
        return SimpleNamespace(
            start_date=start_date,
            end_date=end_date,
            activities_count=2,
            manual_sessions_count=1,
            total_duration_minutes=180,
            total_distance_km=24.5,
            total_elevation_gain_m=900.0,
            measured_load=120.0,
            estimated_load=30.0,
            distance_data_count=2,
            elevation_data_count=1,
            measured_load_data_count=2,
            sessions_count=3,
            total_load=150.0,
        )

    service = SimpleNamespace(calculate=calculate)
    tool = build_training_history_tool(
        service,
        athlete_id,
        reference_date_provider=lambda: date(2026, 11, 9),
    )
    registry = AIToolRegistry()
    registry.register(tool)

    result = registry.execute("training_history", {"nb_days": 7})

    assert result.status == "ok"
    assert calls == [(athlete_id, date(2026, 11, 3), date(2026, 11, 9))]
    assert result.data["period"] == {
        "start_date": "2026-11-03",
        "end_date": "2026-11-09",
        "nb_days": 7,
        "inclusive": True,
    }
    assert result.data["metrics"]["duration_minutes"]["coverage"]["status"] == "unavailable"
    assert result.data["metrics"]["duration_minutes"]["value"] is None
    assert result.data["metrics"]["distance_km"]["coverage"]["status"] == "partial"
    assert result.data["metrics"]["distance_km"]["value"] is None
    assert result.data["metrics"]["elevation_gain_m"]["coverage"]["status"] == "partial"
    assert result.data["metrics"]["training_load"]["total"] == 150.0


def test_training_history_tool_rejects_out_of_range_period():
    service = SimpleNamespace(calculate=lambda *_: None)
    tool = build_training_history_tool(service, uuid4())
    registry = AIToolRegistry()
    registry.register(tool)

    result = registry.execute("training_history", {"nb_days": 366})

    assert result.status == "invalid_arguments"



def test_training_history_tool_requires_explicit_period():
    tool = build_training_history_tool(
        SimpleNamespace(calculate=lambda *_: None),
        uuid4(),
    )
    registry = AIToolRegistry()
    registry.register(tool)

    result = registry.execute("training_history", {})

    assert result.status == "invalid_arguments"
