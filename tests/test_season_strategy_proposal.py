from datetime import date

import pytest

from opencoach.planning import (
    MacrocyclePhase,
    SeasonStrategyProposal,
    StrategyAssumption,
    StrategyDecision,
    StrategyFactReference,
    StrategyRevisionChange,
    StrategyUncertainty,
    TrainingStimulus,
    WeekTrajectory,
)


def create_fact():
    return StrategyFactReference(
        source_path=(
            "athlete.baseline.weekly_distance_km"
        ),
        purpose=(
            "Dimensionner la progression de charge."
        ),
    )


def create_assumption():
    return StrategyAssumption(
        assumption_id="terrain_access",
        description=(
            "L'athlète dispose régulièrement "
            "d'un terrain adapté au dénivelé."
        ),
        impact="medium",
        affected_area="specificity",
    )


def create_decision():
    return StrategyDecision(
        decision_type="load_progression",
        description=(
            "Progression graduelle de la charge "
            "avant le bloc spécifique."
        ),
        rationale=(
            "La baseline actuelle permet une "
            "progression prudente."
        ),
        based_on_facts=(
            "athlete.baseline.weekly_distance_km",
        ),
        based_on_assumptions=(
            "terrain_access",
        ),
    )


def create_phase():
    return MacrocyclePhase(
        phase_type="build",
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            28,
        ),
        objective=(
            "Développer progressivement "
            "la capacité d'entraînement."
        ),
        primary_stimuli=(
            "aerobic_endurance",
            "threshold",
        ),
    )


def create_week():
    return WeekTrajectory(
        week_number=1,
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            7,
        ),
        phase="build",
        target_load=300.0,
        load_min=280.0,
        load_max=320.0,
        target_duration_minutes=300,
        target_distance_km=45.0,
        target_elevation_gain_m=800.0,
        primary_stimuli=(
            TrainingStimulus(
                stimulus_type="threshold",
                priority="high",
            ),
        ),
    )


def create_proposal(
    *,
    revision_changes=(),
):
    return SeasonStrategyProposal(
        summary=(
            "Progression vers la course principale "
            "avec augmentation contrôlée de la spécificité."
        ),
        facts_used=(
            create_fact(),
        ),
        assumptions=(
            create_assumption(),
        ),
        decisions=(
            create_decision(),
        ),
        uncertainties=(
            StrategyUncertainty(
                level="medium",
                description=(
                    "Les seuils physiologiques "
                    "doivent encore être calibrés."
                ),
                affected_area="intensity_prescription",
                resolution_hint=(
                    "Programmer une évaluation physiologique."
                ),
            ),
        ),
        phases=(
            create_phase(),
        ),
        weeks=(
            create_week(),
        ),
        revision_changes=tuple(
            revision_changes
        ),
    )


def test_proposal_separates_facts_assumptions_and_decisions() -> None:
    proposal = create_proposal()

    assert len(
        proposal.facts_used
    ) == 1

    assert len(
        proposal.assumptions
    ) == 1

    assert len(
        proposal.decisions
    ) == 1

    assert proposal.has_assumptions is True


def test_fact_reference_does_not_duplicate_value() -> None:
    fact = create_fact()

    assert (
        fact.source_path
        == "athlete.baseline.weekly_distance_km"
    )

    assert not hasattr(
        fact,
        "value",
    )


def test_decision_cannot_reference_unknown_fact() -> None:
    with pytest.raises(
        ValueError,
        match="fait non déclaré",
    ):
        SeasonStrategyProposal(
            summary="Test.",
            facts_used=(),
            assumptions=(),
            decisions=(
                StrategyDecision(
                    decision_type="load_progression",
                    description="Progression.",
                    rationale="Test.",
                    based_on_facts=(
                        "athlete.baseline.unknown",
                    ),
                ),
            ),
            uncertainties=(),
            phases=(),
            weeks=(),
        )


def test_decision_cannot_reference_unknown_assumption() -> None:
    with pytest.raises(
        ValueError,
        match="hypothèse non déclarée",
    ):
        SeasonStrategyProposal(
            summary="Test.",
            facts_used=(),
            assumptions=(),
            decisions=(
                StrategyDecision(
                    decision_type="load_progression",
                    description="Progression.",
                    rationale="Test.",
                    based_on_assumptions=(
                        "unknown",
                    ),
                ),
            ),
            uncertainties=(),
            phases=(),
            weeks=(),
        )


def test_assumption_ids_must_be_unique() -> None:
    assumption = create_assumption()

    with pytest.raises(
        ValueError,
        match="uniques",
    ):
        SeasonStrategyProposal(
            summary="Test.",
            facts_used=(),
            assumptions=(
                assumption,
                assumption,
            ),
            decisions=(),
            uncertainties=(),
            phases=(),
            weeks=(),
        )


def test_high_uncertainty_is_exposed() -> None:
    proposal = SeasonStrategyProposal(
        summary="Test.",
        facts_used=(),
        assumptions=(),
        decisions=(),
        uncertainties=(
            StrategyUncertainty(
                level="high",
                description=(
                    "Historique insuffisant."
                ),
                affected_area="load_progression",
            ),
        ),
        phases=(),
        weeks=(),
    )

    assert (
        proposal.has_high_uncertainty
        is True
    )


def test_revision_changes_are_explicit() -> None:
    proposal = create_proposal(
        revision_changes=(
            StrategyRevisionChange(
                action="modify",
                target="phase:specific",
                description=(
                    "Avancer le début du bloc spécifique."
                ),
                reason=(
                    "Une nouvelle course prioritaire "
                    "a été ajoutée en mai."
                ),
            ),
        )
    )

    assert proposal.is_revision is True

    assert (
        proposal.revision_changes[0].action
        == "modify"
    )


def test_proposal_contains_no_detailed_sessions() -> None:
    proposal = create_proposal()

    assert not hasattr(
        proposal,
        "sessions",
    )

    assert not hasattr(
        proposal.weeks[0],
        "sessions",
    )
