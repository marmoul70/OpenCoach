from opencoach.coaching.profile_data_evidence import evidence_supports_profile_value


def test_numeric_profile_value_must_match_explicit_evidence():
    assert evidence_supports_profile_value("vma", "Ma VMA est de 15,5 km/h.", 15.5)
    assert evidence_supports_profile_value("weight_kg", "Je pèse 82 kg.", 82)
    assert not evidence_supports_profile_value("vma", "Ma VMA est de 15,5 km/h.", 16)


def test_boolean_is_never_accepted_as_numeric_profile_evidence():
    assert not evidence_supports_profile_value("weekly_sessions", "Je fais 3 séances.", True)


def test_available_days_require_each_day_to_be_named():
    assert evidence_supports_profile_value(
        "available_days",
        "Je suis disponible le lundi, mercredi et vendredi.",
        [0, 2, 4],
    )
    assert not evidence_supports_profile_value(
        "available_days",
        "Je suis disponible le lundi et mercredi.",
        [0, 2, 4],
    )


def test_equipment_brand_and_model_must_both_be_present():
    assert evidence_supports_profile_value(
        "shoe",
        "J'ai acheté des Asics Trabuco 14.",
        {"model": "Trabuco 14", "brand": "Asics"},
    )
    assert not evidence_supports_profile_value(
        "shoe",
        "J'ai acheté des Trabuco 14.",
        {"model": "Trabuco 14", "brand": "Asics"},
    )
