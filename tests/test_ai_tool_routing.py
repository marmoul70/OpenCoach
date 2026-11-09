from opencoach.ai.tool_routing import ALL_COACH_TOOLS, select_coach_tools


def test_history_request_exposes_history_tool_and_proposal_only():
    selected = select_coach_tools("Fais-moi le bilan de mon historique sur 7 jours.")
    assert selected == frozenset({"training_history", "propose_profile_data"})


def test_recovery_request_does_not_expose_training_history_tool():
    selected = select_coach_tools("Analyse ma récupération et mon sommeil.")
    assert "recovery_analysis" in selected
    assert "recovery_status" in selected
    assert "training_history" not in selected


def test_compound_request_keeps_all_required_tool_families():
    selected = select_coach_tools(
        "Analyse ma charge et ma récupération, puis compare mon évolution."
    )
    assert {"training_load", "recovery_analysis", "recovery_status", "training_trends"} <= selected


def test_short_follow_up_uses_recent_user_context():
    selected = select_coach_tools(
        "Et la charge ?",
        history=["Fais-moi un bilan de mon historique sur 14 jours."],
    )
    assert "training_history" in selected
    assert "training_load" in selected


def test_ambiguous_request_falls_back_to_full_catalog():
    assert select_coach_tools("Peux-tu m'aider ?") == ALL_COACH_TOOLS


def test_general_educational_question_exposes_no_tools():
    assert select_coach_tools(
        "Explique-moi la différence entre endurance fondamentale et seuil."
    ) == frozenset()


def test_prohibited_automatic_planning_write_exposes_no_tools():
    assert select_coach_tools(
        "Décale automatiquement ma séance de demain à vendredi."
    ) == frozenset()


def test_direct_provider_access_request_exposes_no_tools():
    assert select_coach_tools(
        "Va chercher directement mes données COROS pour calculer ma charge."
    ) == frozenset()


def test_empty_request_falls_back_to_full_catalog():
    assert select_coach_tools("   ") == ALL_COACH_TOOLS



def test_activity_detail_wording_routes_to_activity_tool():
    selected = select_coach_tools("Détaille ma séance du 8 novembre.")
    assert "activity_detail" in selected
    assert "race_calendar" not in selected


def test_achilles_pain_before_training_advice_routes_to_constraints():
    selected = select_coach_tools(
        "J'ai mal au tendon d'Achille, quelle séance puis-je faire aujourd'hui ?"
    )
    assert "active_constraints" in selected
    assert {"recovery_analysis", "recovery_status"} <= selected



def test_router_never_hides_expected_tools_from_evaluation_fixture():
    import json
    from pathlib import Path

    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "ai_model_evaluation_cases.json"
    )
    cases = json.loads(fixture.read_text(encoding="utf-8"))

    for case in cases:
        turns = case.get("conversation") or []
        if turns:
            user_turns = [turn["content"] for turn in turns if turn["role"] == "user"]
            question = user_turns[-1]
            history = user_turns[:-1]
        else:
            question = case["prompt"]
            history = []

        selected = select_coach_tools(question, history=history)
        expected = {call["tool"] for call in case["expected_tool_calls"]}
        assert expected.issubset(selected), case["id"]
