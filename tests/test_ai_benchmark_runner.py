import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ai.benchmark_models import (
    score_response,
    build_case_conversation,
    summarize,
    validate_local_base_url,
    build_tool_definitions,
    build_system_prompt,
    build_benchmark_system_prompt,
    TOOL_PROFILES,
    filter_cases_for_tool_profile,
    ARGUMENT_MODELS,
)


def test_benchmark_builds_multi_turn_clarification_conversation() -> None:
    messages = build_case_conversation({
        "prompt": "Sur les 7 derniers jours.",
        "conversation": [
            {"role": "user", "content": "Fais-moi le bilan de mon historique."},
            {"role": "assistant", "content": "Sur combien de jours ?"},
            {"role": "user", "content": "Sur 7 jours."},
        ],
    })

    assert [message.role for message in messages] == ["user", "assistant", "user"]
    assert messages[-1].content == "Sur 7 jours."


def test_benchmark_scores_exact_tool_and_arguments() -> None:
    case = {
        "id": "history",
        "expected_tool_calls": [
            {"tool": "training_history", "arguments": {"nb_days": 7}}
        ],
        "expected_clarification": None,
    }

    result = score_response(
        case,
        [{"name": "training_history", "arguments": {"nb_days": 7}}],
        "",
    )

    assert result["tool_selection_pass"] is True
    assert result["argument_validation_pass"] is True


def test_benchmark_rejects_wrong_arguments_and_extra_tool_calls() -> None:
    case = {
        "id": "history",
        "expected_tool_calls": [
            {"tool": "training_history", "arguments": {"nb_days": 7}}
        ],
        "expected_clarification": None,
    }

    result = score_response(
        case,
        [
            {"name": "training_history", "arguments": {"nb_days": 14}},
            {"name": "training_load", "arguments": {"nb_days": 7}},
        ],
        "",
    )

    assert result["tool_selection_pass"] is False
    assert result["argument_validation_pass"] is True


def test_benchmark_marks_out_of_range_generated_arguments_invalid() -> None:
    case = {
        "id": "history_out_of_range",
        "expected_tool_calls": [],
        "expected_clarification": "Signaler la limite autorisée.",
    }

    result = score_response(
        case,
        [{"name": "training_history", "arguments": {"nb_days": 500}}],
        "",
    )

    assert result["tool_selection_pass"] is False
    assert result["argument_validation_pass"] is False
    assert result["actual_tool_calls"][0]["arguments_valid"] is False


def test_benchmark_checks_clarification_only_when_expected_on_first_turn() -> None:
    case = {
        "id": "clarification",
        "expected_tool_calls": [],
        "expected_clarification": "Demander la période.",
    }

    result = score_response(case, [], "Sur combien de jours souhaites-tu le bilan ?")

    assert result["clarification_checkable"] is True
    assert result["clarification_pass"] is True


def test_benchmark_does_not_score_second_turn_clarification_before_tool_result() -> None:
    case = {
        "id": "race",
        "expected_tool_calls": [{"tool": "race_calendar", "arguments": {}}],
        "expected_clarification": "Demander history_days après le calendrier.",
        "clarification_stage": "after_tool_result",
    }

    result = score_response(
        case,
        [{"name": "race_calendar", "arguments": {}}],
        "",
    )

    assert result["tool_selection_pass"] is True
    assert result["clarification_checkable"] is False


def test_benchmark_summary_reports_latency_and_accuracy() -> None:
    rows = [
        {"model": "qwen3:8b", "status": "ok", "latency_ms": 100,
         "tool_selection_pass": True, "argument_validation_pass": True, "clarification_checkable": False,
         "clarification_pass": None},
        {"model": "qwen3:8b", "status": "ok", "latency_ms": 200,
         "tool_selection_pass": False, "argument_validation_pass": False, "clarification_checkable": True,
         "clarification_pass": True},
    ]

    result = summarize(rows, "qwen3:8b")

    assert result["tool_selection_accuracy"] == 0.5
    assert result["argument_validation_accuracy"] == 0.5
    assert result["clarification_accuracy"] == 1.0
    assert result["latency_ms_p50"] == 100


def test_benchmark_refuses_remote_endpoints() -> None:
    import pytest

    with pytest.raises(ValueError, match="loopback"):
        validate_local_base_url("https://example.com")


def test_benchmark_accepts_localhost_and_loopback() -> None:
    assert validate_local_base_url("http://localhost:11434/") == "http://localhost:11434"
    assert validate_local_base_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"


def test_benchmark_exposes_the_complete_production_read_tool_catalog() -> None:
    definitions = build_tool_definitions()
    names = {item.name for item in definitions}

    assert len(definitions) == 13
    assert {
        "athlete_training_profile",
        "active_constraints",
        "weekly_plan_context",
        "race_calendar",
        "race_preparation_analysis",
        "planned_sessions",
        "session_execution_review",
        "activity_detail",
        "training_history",
        "training_load",
        "recovery_status",
        "recovery_analysis",
        "training_trends",
    } == names

    descriptions = {item.name: item.description for item in definitions}
    assert "demande-la à l'utilisateur et attends sa réponse" in descriptions["training_history"]
    assert "demande la période si elle manque et attends la réponse" in descriptions["training_load"]
    assert "deux durées si elles manquent et attends la réponse" in descriptions["training_trends"]


def test_benchmark_supports_all_and_focused_tool_profiles() -> None:
    all_tools = build_tool_definitions("all")
    focused_tools = build_tool_definitions("history")

    assert len(all_tools) == 13
    assert [tool.name for tool in focused_tools] == [
        "training_history", "training_load", "recovery_analysis"
    ]
    assert set(TOOL_PROFILES["history"]).issubset(ARGUMENT_MODELS)


def test_focused_tool_profile_filters_incompatible_scenarios() -> None:
    cases = [
        {"id": "history_missing_period", "expected_tool_calls": []},
        {"id": "history_explicit", "expected_tool_calls": [{"tool": "training_history"}]},
        {"id": "load_explicit", "expected_tool_calls": [{"tool": "training_load"}]},
        {"id": "recovery_missing", "expected_tool_calls": [{"tool": "recovery_analysis"}]},
        {"id": "trends_missing", "expected_tool_calls": []},
        {"id": "general_question", "expected_tool_calls": []},
        {"id": "race_calendar", "expected_tool_calls": [{"tool": "race_calendar"}]},
    ]

    selected = filter_cases_for_tool_profile(cases, "history")
    assert [case["id"] for case in selected] == [
        "history_missing_period", "history_explicit", "load_explicit", "recovery_missing"
    ]
    assert filter_cases_for_tool_profile(cases, "all") == cases


def test_benchmark_supports_production_and_minimal_prompt_profiles() -> None:
    production = build_system_prompt("production")
    minimal = build_system_prompt("minimal")

    assert "OpenCoach" in production
    assert len(minimal) < len(production)
    assert "training_history" in minimal
    assert "ne déduis jamais une période" in minimal.lower()


def test_benchmark_context_is_embedded_in_system_message_not_a_fake_user_turn() -> None:
    case = {"reference_date": "2026-11-09"}
    prompt = build_benchmark_system_prompt(case, "minimal")

    assert "Date de référence : 2026-11-09" in prompt
    assert "sans donnée personnelle" in prompt


def test_expected_fixture_arguments_validate_against_production_schemas() -> None:
    import json
    from pathlib import Path

    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "ai_model_evaluation_cases.json"
    )
    cases = json.loads(fixture.read_text(encoding="utf-8"))

    for case in cases:
        for call in case["expected_tool_calls"]:
            model = ARGUMENT_MODELS[call["tool"]]
            model.model_validate(call["arguments"])
