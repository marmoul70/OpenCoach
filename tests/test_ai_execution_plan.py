from datetime import date

from opencoach.ai.execution_plan import build_coach_execution_plan


REFERENCE_DATE = date(2026, 11, 10)


def test_history_period_is_extracted_and_planned_without_model_tool_calling():
    plan = build_coach_execution_plan(
        "Analyse mon historique sur les 7 derniers jours.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.clarification is None
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("training_history", {"nb_days": 7})
    ]


def test_history_clarification_is_deterministic_when_period_is_missing():
    plan = build_coach_execution_plan(
        "Fais-moi le bilan de mon historique d'entraînement.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert "combien de jours" in plan.clarification


def test_history_period_is_carried_from_the_clarification_turn():
    plan = build_coach_execution_plan(
        "Sur les 7 derniers jours.",
        history=["Fais-moi le bilan de mon historique d'entraînement."],
        assistant_history=["Sur combien de jours souhaites-tu que j'analyse ton historique ?"],
        reference_date=REFERENCE_DATE,
    )
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("training_history", {"nb_days": 7})
    ]


def test_out_of_range_history_is_rejected_before_tool_execution():
    plan = build_coach_execution_plan(
        "Analyse mon historique sur 500 jours.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert "1 à 365 jours" in plan.clarification


def test_current_recovery_uses_python_default_date_and_status_tool():
    plan = build_coach_execution_plan(
        "Quel est mon état de récupération aujourd'hui ?",
        reference_date=REFERENCE_DATE,
    )
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("recovery_status", {})
    ]


def test_injury_advice_executes_constraints_before_recovery_status():
    plan = build_coach_execution_plan(
        "J'ai mal au tendon d'Achille, quelle séance puis-je faire aujourd'hui ?",
        reference_date=REFERENCE_DATE,
    )
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("active_constraints", {}),
        ("recovery_status", {}),
    ]


def test_activity_date_is_extracted_without_asking_the_model():
    plan = build_coach_execution_plan(
        "Détaille ma séance du 8 novembre.",
        reference_date=REFERENCE_DATE,
    )
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("activity_detail", {"activity_date": "2026-11-08"})
    ]


def test_activity_request_without_a_date_asks_for_clarification():
    plan = build_coach_execution_plan(
        "Détaille ma dernière activité.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert "date exacte" in plan.clarification


def test_general_question_does_not_select_or_execute_any_business_tool():
    plan = build_coach_execution_plan(
        "Explique-moi la différence entre endurance fondamentale et seuil.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert plan.clarification is None


def test_external_provider_access_is_refused_before_any_tool_execution():
    plan = build_coach_execution_plan(
        "Va chercher directement mes données COROS pour calculer ma charge.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert "ne consulte pas directement" in plan.clarification


def test_load_period_is_planned_with_exact_user_supplied_duration():
    plan = build_coach_execution_plan(
        "Donne-moi ma charge d'entraînement sur les 14 derniers jours.",
        reference_date=REFERENCE_DATE,
    )
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("training_load", {"nb_days": 14})
    ]


def test_trends_requires_two_explicit_periods():
    plan = build_coach_execution_plan(
        "Compare mes tendances d'entraînement.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert "deux périodes" in plan.clarification


def test_planned_sessions_uses_the_exact_explicit_date_range():
    plan = build_coach_execution_plan(
        "Quelles séances sont planifiées du 9 au 15 novembre 2026 ?",
        reference_date=REFERENCE_DATE,
    )
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("planned_sessions", {
            "start_date": "2026-11-09",
            "end_date": "2026-11-15",
        })
    ]


def test_profile_value_is_proposed_with_exact_user_evidence():
    question = "Ma VMA est de 15,5 km/h."
    plan = build_coach_execution_plan(question, reference_date=REFERENCE_DATE)
    assert len(plan.calls) == 1
    assert plan.calls[0].name == "propose_profile_data"
    assert plan.calls[0].arguments == {
        "field_key": "vma",
        "value": 15.5,
        "evidence": question,
    }



def test_ambiguous_help_request_does_not_execute_fallback_catalog():
    plan = build_coach_execution_plan(
        "Peux-tu m'aider ?",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert plan.clarification is None
