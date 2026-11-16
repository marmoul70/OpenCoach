from opencoach.coaching.assistant.argument_evidence import validate_period_argument_evidence


def test_period_evidence_checks_user_value_without_duplicating_domain_bounds():
    assert validate_period_argument_evidence(
        "training_load",
        {"nb_days": 91},
        ["Analyse ma charge sur 91 jours."],
    ) is None

    assert validate_period_argument_evidence(
        "training_load",
        {"nb_days": 90},
        ["Analyse ma charge sur 91 jours."],
    ) is not None



def test_weekly_bilan_does_not_inject_a_period_into_ai_evidence():
    from opencoach.coaching.assistant.argument_evidence import extract_explicit_periods

    assert extract_explicit_periods(["Fais-moi le bilan de ma semaine."]) == []
