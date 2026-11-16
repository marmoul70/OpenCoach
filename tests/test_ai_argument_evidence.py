from opencoach.ai.argument_evidence import validate_period_argument_evidence


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
