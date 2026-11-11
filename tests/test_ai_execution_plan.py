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


def test_two_period_trend_clarification_restores_original_intent_after_intermediate_reply():
    plan = build_coach_execution_plan(
        "7 jours",
        history=[
            "Compare mes tendances de charge d'entraînement.",
            "2 jours",
        ],
        assistant_history=[
            "Quelles périodes souhaites-tu comparer ?",
            "Pour comparer ces tendances, indique la durée des deux périodes (par exemple 7 jours et 14 jours).",
        ],
        reference_date=REFERENCE_DATE,
    )

    assert plan.clarification is None
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("training_load", {"nb_days": 7}),
        ("training_trends", {"nb_days": 2, "comparison_days": 7}),
    ]


def test_short_clarification_answer_does_not_reuse_unrelated_old_intent():
    plan = build_coach_execution_plan(
        "7 jours",
        history=[
            "Analyse ma charge sur 14 jours.",
            "Merci pour cette analyse.",
        ],
        assistant_history=[
            "Voici ton bilan de charge.",
            "Quelle durée souhaites-tu pour une autre analyse ?",
        ],
        reference_date=REFERENCE_DATE,
    )

    assert plan.calls == ()
    assert plan.clarification is None


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


def test_latest_activity_request_without_a_date_selects_latest_activity():
    plan = build_coach_execution_plan(
        "Détaille ma dernière activité.",
        reference_date=REFERENCE_DATE,
    )
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("activity_detail", {"latest": True})
    ]
    assert plan.clarification is None


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



def test_compound_charge_and_recovery_asks_for_missing_charge_period_first():
    plan = build_coach_execution_plan(
        "Analyse ma charge et ma récupération.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert "combien de jours" in plan.clarification


def test_planned_sessions_without_dates_asks_before_weekly_context_lookup():
    plan = build_coach_execution_plan(
        "Quelles sont mes séances planifiées ?",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert "dates de début et de fin" in plan.clarification



def test_short_thanks_after_completed_answer_does_not_repeat_previous_tool():
    plan = build_coach_execution_plan(
        "Merci !",
        history=["Analyse mon historique sur les 7 derniers jours."],
        assistant_history=["Voici ton bilan sur les 7 derniers jours."],
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert plan.clarification is None



def test_injury_for_tomorrow_uses_the_requested_date_for_both_safety_tools():
    plan = build_coach_execution_plan(
        "J'ai mal au tendon, quelle séance puis-je faire demain ?",
        reference_date=REFERENCE_DATE,
    )
    assert [(call.name, call.arguments) for call in plan.calls] == [
        ("active_constraints", {"target_date": "2026-11-11"}),
        ("recovery_status", {"target_date": "2026-11-11"}),
    ]


def test_new_load_request_does_not_inherit_recovery_button_periods():
    plan = build_coach_execution_plan(
        "Analyse ma charge d'entraînement.",
        history=[
            "Fais un bilan de mon état de forme et de ma fatigue. Analyse le sommeil, la HRV, la fréquence cardiaque au repos, le stress et la charge sur 7, 14 et 30 jours."
        ],
        assistant_history=[
            "Le bilan de récupération utilise les fenêtres de 7, 14 et 30 jours."
        ],
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert "combien de jours" in plan.clarification



def test_general_trail_explanation_does_not_execute_race_tools():
    plan = build_coach_execution_plan(
        "Explique-moi ce qu'est un trail.",
        reference_date=REFERENCE_DATE,
    )
    assert plan.calls == ()
    assert plan.clarification is None
