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
