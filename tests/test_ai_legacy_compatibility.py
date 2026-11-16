"""Contrats de compatibilité : les anciens chemins IA ne contiennent aucun comportement."""

def test_legacy_conversation_modules_are_direct_coach_aliases():
    from opencoach.ai import argument_evidence as legacy_evidence
    from opencoach.ai import execution_plan as legacy_plan
    from opencoach.ai import tool_routing as legacy_routing
    from opencoach.coaching.assistant import (
        argument_evidence as coach_evidence,
        execution_plan as coach_plan,
        tool_routing as coach_routing,
    )

    assert legacy_evidence.validate_period_argument_evidence is coach_evidence.validate_period_argument_evidence
    assert legacy_evidence.extract_explicit_periods is coach_evidence.extract_explicit_periods
    assert legacy_plan.build_coach_execution_plan is coach_plan.build_coach_execution_plan
    assert legacy_routing.select_coach_tools is coach_routing.select_coach_tools
    assert legacy_routing.ALL_COACH_TOOLS is coach_routing.ALL_COACH_TOOLS


def test_legacy_profile_proposal_module_is_a_direct_coach_alias():
    from opencoach.ai import data_proposals as legacy
    from opencoach.coaching import profile_data_proposals as coach

    assert legacy.create_profile_data_proposal is coach.create_profile_data_proposal
    assert legacy.confirm_profile_data_proposal is coach.confirm_profile_data_proposal
    assert legacy.reject_profile_data_proposal is coach.reject_profile_data_proposal
