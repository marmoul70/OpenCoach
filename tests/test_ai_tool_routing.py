from opencoach.ai.tool_routing import ALL_COACH_TOOLS, select_coach_tools


def test_history_request_exposes_history_tool_without_profile_write_tool():
    selected = select_coach_tools("Fais-moi le bilan de mon historique sur 7 jours.")
    assert selected == frozenset({"training_history"})


def test_recovery_request_does_not_expose_training_history_tool():
    selected = select_coach_tools("Analyse ma récupération et mon sommeil.")
    assert "recovery_analysis" in selected
    assert "recovery_status" in selected
    assert "training_history" not in selected


def test_compound_request_keeps_only_tools_with_satisfied_period_requirements():
    selected = select_coach_tools(
        "Analyse ma charge et ma récupération, puis compare mon évolution."
    )
    assert selected == frozenset({"recovery_analysis", "recovery_status"})

    selected_with_periods = select_coach_tools(
        "Analyse ma charge sur 14 jours, ma récupération et compare mon évolution sur 7 jours et 14 jours."
    )
    assert {"training_load", "recovery_analysis", "recovery_status", "training_trends"} <= selected_with_periods


def test_short_follow_up_uses_recent_user_context():
    selected = select_coach_tools(
        "Et la charge ?",
        history=["Fais-moi un bilan de mon historique sur 14 jours."],
    )
    assert "training_history" in selected
    assert "training_load" in selected


def test_ambiguous_request_keeps_catalog_except_unqualified_period_tools():
    assert select_coach_tools("Peux-tu m'aider ?") == (
        ALL_COACH_TOOLS
        - {
            "training_history",
            "training_load",
            "training_trends",
            "race_preparation_analysis",
        }
    )


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


def test_empty_request_does_not_expose_unqualified_period_tools():
    assert select_coach_tools("   ") == (
        ALL_COACH_TOOLS
        - {
            "training_history",
            "training_load",
            "training_trends",
            "race_preparation_analysis",
        }
    )



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
            assistant_turns = [turn["content"] for turn in turns if turn["role"] == "assistant"]
            question = user_turns[-1]
            history = user_turns[:-1]
        else:
            question = case["prompt"]
            history = []
            assistant_turns = []

        selected = select_coach_tools(
            question, history=history, assistant_history=assistant_turns
        )
        expected = {call["tool"] for call in case["expected_tool_calls"]}
        assert expected.issubset(selected), case["id"]



def test_missing_history_period_hides_history_tool():
    assert select_coach_tools(
        "Fais-moi le bilan de mon historique d'entraînement."
    ) == frozenset()


def test_relative_history_period_exposes_history_tool():
    assert select_coach_tools(
        "Analyse mon historique sur les 7 derniers jours."
    ) == frozenset({"training_history"})


def test_short_numeric_clarification_reexposes_history_tool():
    assert select_coach_tools(
        "7",
        history=["Fais-moi le bilan de mon historique."],
        assistant_history=["Sur combien de jours souhaites-tu le bilan ?"],
    ) == frozenset({"training_history"})


def test_missing_period_hides_only_period_tools_from_compound_request():
    selected = select_coach_tools("Analyse ma charge et ma récupération.")
    assert selected == frozenset({"recovery_analysis", "recovery_status"})


def test_trends_tool_requires_two_explicit_periods():
    assert select_coach_tools("Compare mes tendances d'entraînement.") == frozenset()
    assert select_coach_tools(
        "Compare mes tendances sur 7 jours et 14 jours."
    ) == frozenset({"training_trends"})


def test_race_preparation_waits_for_history_period_but_keeps_race_calendar():
    assert select_coach_tools(
        "Analyse ma préparation pour ma prochaine course."
    ) == frozenset({"race_calendar"})
    assert select_coach_tools(
        "Analyse ma préparation sur les 30 derniers jours pour ma prochaine course."
    ) == frozenset({"race_calendar", "race_preparation_analysis"})



def test_trends_tool_reopens_after_second_period_clarification():
    selected = select_coach_tools(
        "14 jours",
        history=["Compare mes tendances sur 7 jours."],
        assistant_history=[
            "Pour comparer tes tendances, indique la durée des deux périodes."
        ],
    )
    assert selected == frozenset({"training_trends"})
