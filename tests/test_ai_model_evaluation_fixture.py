import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "ai_model_evaluation_cases.json"
)


def test_ai_model_evaluation_corpus_has_unique_ids_and_valid_contract() -> None:
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert len(cases) >= 10
    identifiers = [case["id"] for case in cases]
    assert len(identifiers) == len(set(identifiers))

    for case in cases:
        assert case["category"]
        assert case["prompt"].strip()
        assert isinstance(case["expected_tool_calls"], list)
        assert isinstance(case["forbidden_behaviors"], list)
        assert case["forbidden_behaviors"]

        if "conversation" in case:
            assert case["conversation"]
            assert all(turn["role"] in {"user", "assistant"} for turn in case["conversation"])
            assert all(turn["content"].strip() for turn in case["conversation"])
            assert case["conversation"][-1]["role"] == "user"

        for call in case["expected_tool_calls"]:
            assert set(call) == {"tool", "arguments"}
            assert call["tool"].strip()
            assert isinstance(call["arguments"], dict)

        if case["expected_clarification"] is not None:
            assert case["expected_clarification"].strip()


def test_ai_model_evaluation_corpus_covers_critical_safety_categories() -> None:
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    categories = {case["category"] for case in cases}

    assert {
        "clarification",
        "argument_validation",
        "missing_data",
        "safety",
        "architecture",
        "authorization",
        "no_tool",
    }.issubset(categories)
