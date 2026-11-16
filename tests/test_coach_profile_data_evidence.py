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


def test_profile_proposal_evidence_must_belong_to_user_messages():
    from opencoach.coaching.profile_data_evidence import validate_profile_proposal_evidence

    assert validate_profile_proposal_evidence(
        "vma",
        "Ma VMA est de 15,5 km/h.",
        15.5,
        ["Bonjour", "Ma VMA est de 15,5 km/h."],
    )
    assert not validate_profile_proposal_evidence(
        "vma",
        "Ma VMA est de 15,5 km/h.",
        15.5,
        ["Ma VMA est de 15 km/h."],
    )


def test_profile_proposal_evidence_rejects_unsupported_values():
    from opencoach.coaching.profile_data_evidence import validate_profile_proposal_evidence

    assert not validate_profile_proposal_evidence(
        "vma",
        "Ma VMA est de 15,5 km/h.",
        16,
        ["Ma VMA est de 15,5 km/h."],
    )

def test_numeric_profile_proposal_is_extracted_only_from_explicit_wording():
    from opencoach.coaching.profile_data_evidence import extract_numeric_profile_proposal

    assert extract_numeric_profile_proposal("Ma VMA est de 15,5 km/h.") == (
        {
            "field_key": "vma",
            "value": 15.5,
            "evidence": "Ma VMA est de 15,5 km/h.",
        },
        None,
    )
    assert extract_numeric_profile_proposal("Je pèse 82 kg.") == (
        {
            "field_key": "weight_kg",
            "value": 82.0,
            "evidence": "Je pèse 82 kg.",
        },
        None,
    )


def test_numeric_profile_proposal_does_not_guess_missing_units_or_values():
    from opencoach.coaching.profile_data_evidence import extract_numeric_profile_proposal

    proposal, clarification = extract_numeric_profile_proposal("Ma VMA est de 15,5.")
    assert proposal is None
    assert "aucune donnée n'a été proposée" in clarification


def test_profile_proposal_evidence_cannot_be_stitched_across_messages():
    from opencoach.coaching.profile_data_evidence import validate_profile_proposal_evidence

    evidence = r"Ma VMA est de\\n15,5 km/h."
    assert not validate_profile_proposal_evidence(
        "vma",
        evidence,
        15.5,
        ["Ma VMA est de", "15,5 km/h."],
    )
