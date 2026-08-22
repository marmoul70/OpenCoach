from datetime import date

import pytest

from opencoach.planning import (
    SeasonStrategistInvalidResponseError,
    build_season_strategy_proposal_schema,
    parse_season_strategy_proposal,
)


def create_valid_payload():
    return {
        "summary": "Progression vers la course cible.",
        "facts_used": [
            {
                "source_path": (
                    "athlete.baseline.weekly_training_load"
                ),
                "purpose": (
                    "Dimensionner la progression."
                ),
            },
        ],
        "assumptions": [],
        "decisions": [
            {
                "decision_type": "load_progression",
                "description": (
                    "Augmenter progressivement la charge."
                ),
                "rationale": (
                    "La baseline permet une progression contrôlée."
                ),
                "based_on_facts": [
                    "athlete.baseline.weekly_training_load",
                ],
                "based_on_assumptions": [],
            },
        ],
        "uncertainties": [],
        "phases": [
            {
                "phase_type": "build",
                "start_date": "2027-03-01",
                "end_date": "2027-03-28",
                "objective": (
                    "Développer la capacité d'entraînement."
                ),
                "primary_stimuli": [
                    "aerobic_endurance",
                    "threshold",
                ],
            },
        ],
        "weeks": [
            {
                "week_number": 1,
                "start_date": "2027-03-01",
                "end_date": "2027-03-07",
                "phase": "build",
                "target_load": 330.0,
                "load_min": 320.0,
                "load_max": 340.0,
                "target_duration_minutes": 320,
                "target_distance_km": 48.0,
                "target_elevation_gain_m": 1100.0,
                "primary_stimuli": [
                    {
                        "stimulus_type": (
                            "aerobic_endurance"
                        ),
                        "priority": "high",
                        "target_exposure_minutes": None,
                        "notes": None,
                    },
                ],
                "recovery_week": False,
                "status": "planned",
                "notes": None,
            },
        ],
        "revision_changes": [],
    }


def test_schema_is_strict_object() -> None:
    schema = (
        build_season_strategy_proposal_schema()
    )

    assert schema["type"] == "object"

    assert (
        schema["additionalProperties"]
        is False
    )

    assert "summary" in (
        schema["required"]
    )

    assert "weeks" in (
        schema["required"]
    )


def test_valid_payload_builds_proposal() -> None:
    proposal = parse_season_strategy_proposal(
        create_valid_payload()
    )

    assert (
        proposal.summary
        == "Progression vers la course cible."
    )

    assert len(
        proposal.phases
    ) == 1

    assert len(
        proposal.weeks
    ) == 1


def test_parser_converts_iso_dates() -> None:
    proposal = parse_season_strategy_proposal(
        create_valid_payload()
    )

    assert (
        proposal.phases[0].start_date
        == date(
            2027,
            3,
            1,
        )
    )

    assert (
        proposal.weeks[0].end_date
        == date(
            2027,
            3,
            7,
        )
    )


def test_unknown_top_level_field_is_rejected() -> None:
    payload = create_valid_payload()

    payload["invented"] = "bad"

    with pytest.raises(
        SeasonStrategistInvalidResponseError,
        match="champs inconnus",
    ):
        parse_season_strategy_proposal(
            payload
        )


def test_missing_required_field_is_rejected() -> None:
    payload = create_valid_payload()

    del payload["summary"]

    with pytest.raises(
        SeasonStrategistInvalidResponseError,
        match="champs requis",
    ):
        parse_season_strategy_proposal(
            payload
        )


def test_unknown_phase_type_is_rejected() -> None:
    payload = create_valid_payload()

    payload["phases"][0][
        "phase_type"
    ] = "magic_phase"

    with pytest.raises(
        SeasonStrategistInvalidResponseError,
        match="valeur inconnue",
    ):
        parse_season_strategy_proposal(
            payload
        )


def test_invalid_date_is_rejected() -> None:
    payload = create_valid_payload()

    payload["weeks"][0][
        "start_date"
    ] = "not-a-date"

    with pytest.raises(
        SeasonStrategistInvalidResponseError,
        match="date ISO",
    ):
        parse_season_strategy_proposal(
            payload
        )


def test_invalid_load_envelope_is_rejected() -> None:
    payload = create_valid_payload()

    payload["weeks"][0][
        "load_min"
    ] = 400.0

    payload["weeks"][0][
        "load_max"
    ] = 300.0

    with pytest.raises(
        SeasonStrategistInvalidResponseError,
        match="contrat métier",
    ):
        parse_season_strategy_proposal(
            payload
        )


def test_boolean_is_not_accepted_as_integer() -> None:
    payload = create_valid_payload()

    payload["weeks"][0][
        "week_number"
    ] = True

    with pytest.raises(
        SeasonStrategistInvalidResponseError,
        match="entier",
    ):
        parse_season_strategy_proposal(
            payload
        )
