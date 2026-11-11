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
    assert registry.execution_results == (result,)


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


def test_registry_restricts_both_visible_and_executable_tools():
    registry = AIToolRegistry()
    registry.register(AITool(
        name="visible",
        description="Outil visible.",
        arguments_model=EchoArguments,
        handler=lambda args: {"value": args.value},
    ))
    registry.register(AITool(
        name="hidden",
        description="Outil masqué.",
        arguments_model=EchoArguments,
        handler=lambda args: {"value": args.value},
    ))

    registry.restrict_to({"visible"})

    assert [item["name"] for item in registry.definitions()] == ["visible"]
    blocked = registry.execute("hidden", {"value": 2})
    accepted = registry.execute("visible", {"value": 3})
    assert blocked.status == "not_found"
    assert accepted.status == "ok"


def test_registry_does_not_expose_internal_exception_details(caplog):
    import logging

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
    assert result.metadata["business_tool_executed"] is True
    assert result.metadata["error_type"] == "RuntimeError"
    assert "Échec d'exécution de l'outil coach 'failure'" in caplog.text
    assert "database password must not leak" in caplog.text


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


def test_training_history_tool_rejects_out_of_range_period_without_calling_service():
    calls = []
    service = SimpleNamespace(calculate=lambda *args: calls.append(args))
    tool = build_training_history_tool(service, uuid4())
    registry = AIToolRegistry()
    registry.register(tool)

    for nb_days in (366, 500):
        result = registry.execute("training_history", {"nb_days": nb_days})
        assert result.status == "invalid_arguments"

    assert calls == []



def test_training_history_tool_requires_explicit_period():
    tool = build_training_history_tool(
        SimpleNamespace(calculate=lambda *_: None),
        uuid4(),
    )
    registry = AIToolRegistry()
    registry.register(tool)

    result = registry.execute("training_history", {})

    assert result.status == "invalid_arguments"


def test_argument_evidence_guard_blocks_unrequested_or_out_of_range_periods():
    from opencoach.ai.argument_evidence import validate_period_argument_evidence

    assert validate_period_argument_evidence("training_history", {"nb_days": 7}, ["Fais-moi le bilan de mon historique."]) == "Sur combien de jours souhaites-tu que j'analyse ton historique ?"
    assert validate_period_argument_evidence("training_history", {"nb_days": 500}, ["Analyse mon historique sur 500 jours."]).startswith("La période demandée (500 jours) dépasse les limites")
    assert validate_period_argument_evidence("training_history", {"nb_days": 7}, ["Analyse mon historique sur 7 jours."]) is None
    assert validate_period_argument_evidence("training_history", {"nb_days": 7}, ["Analyse mon historique sur les 7 derniers jours."]) is None
    assert validate_period_argument_evidence("training_history", {"nb_days": 7}, ["Fais-moi le bilan de mon historique.", "7"], ["Sur combien de jours souhaites-tu ton historique ?"]) is None
    assert validate_period_argument_evidence("training_history", {"nb_days": 14}, ["Donne ma charge sur 14 jours.", "Fais-moi le bilan de mon historique."]) == "Sur combien de jours souhaites-tu que j'analyse ton historique ?"


def test_argument_evidence_guard_requires_both_trend_periods():
    from opencoach.ai.argument_evidence import validate_period_argument_evidence

    assert validate_period_argument_evidence("training_trends", {"nb_days": 7, "comparison_days": 7}, ["Compare mes tendances d'entraînement."]).startswith("Pour comparer tes tendances")
    assert validate_period_argument_evidence("training_trends", {"nb_days": 7, "comparison_days": 14}, ["Compare mes tendances sur 7 jours avec les 14 jours précédents."]) is None
    assert validate_period_argument_evidence("training_trends", {"nb_days": 7, "comparison_days": 7}, ["Compare mes tendances sur 7 jours avec les 14 jours précédents."]).startswith("Les durées proposées")



def test_argument_evidence_guard_covers_race_preparation_history_days():
    from opencoach.ai.argument_evidence import validate_period_argument_evidence

    assert validate_period_argument_evidence(
        "race_preparation_analysis",
        {"history_days": 30},
        ["Analyse ma préparation pour ma prochaine course."],
    ).startswith("Sur combien de jours d'historique")
    assert validate_period_argument_evidence(
        "race_preparation_analysis",
        {"history_days": 30},
        ["Analyse ma préparation sur les 30 derniers jours pour ma prochaine course."],
    ) is None


def test_argument_evidence_guard_reuses_period_only_for_short_contextual_follow_up():
    from opencoach.ai.argument_evidence import validate_period_argument_evidence

    assert validate_period_argument_evidence(
        "training_load",
        {"nb_days": 14},
        ["Fais-moi le bilan de mon historique sur 14 jours.", "Et la charge ?"],
        ["Voici le bilan de ton historique."],
    ) is None



def test_trend_period_evidence_combines_two_clarification_turns():
    from opencoach.ai.argument_evidence import (
        extract_explicit_periods,
        validate_period_argument_evidence,
    )

    user_messages = [
        "Compare mes tendances sur 7 jours.",
        "14 jours",
    ]
    assistant_messages = [
        "Pour comparer tes tendances, indique la durée des deux périodes."
    ]

    assert extract_explicit_periods(user_messages, assistant_messages) == [7, 14]
    assert validate_period_argument_evidence(
        "training_trends",
        {"nb_days": 7, "comparison_days": 14},
        user_messages,
        assistant_messages,
    ) is None



def test_planned_sessions_guard_requires_exact_user_date_range():
    from opencoach.ai.argument_evidence import (
        extract_explicit_date_range,
        validate_period_argument_evidence,
    )

    user_messages = [
        "Quelles séances sont planifiées du 9 au 15 novembre 2026 ?"
    ]
    expected = {"start_date": "2026-11-09", "end_date": "2026-11-15"}

    assert extract_explicit_date_range(user_messages) == (
        date(2026, 11, 9),
        date(2026, 11, 15),
    )
    assert validate_period_argument_evidence(
        "planned_sessions", expected, user_messages
    ) is None
    assert validate_period_argument_evidence(
        "planned_sessions",
        {"start_date": "2026-11-10", "end_date": "2026-11-16"},
        user_messages,
    ).startswith("Les dates proposées ne correspondent pas")
    assert validate_period_argument_evidence(
        "planned_sessions",
        expected,
        ["Quelles sont mes séances planifiées ?"],
    ).startswith("Quelles sont les dates")
