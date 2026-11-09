from scripts.ai.benchmark_models import score_response, summarize


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
         "tool_selection_pass": True, "clarification_checkable": False,
         "clarification_pass": None},
        {"model": "qwen3:8b", "status": "ok", "latency_ms": 200,
         "tool_selection_pass": False, "clarification_checkable": True,
         "clarification_pass": True},
    ]

    result = summarize(rows, "qwen3:8b")

    assert result["tool_selection_accuracy"] == 0.5
    assert result["clarification_accuracy"] == 1.0
    assert result["latency_ms_p50"] == 100
