from types import SimpleNamespace

from opencoach.coaching.constraint_impact import evaluate_running_restriction


def test_running_restriction_blocks_running_and_allows_only_explicit_cross_training():
    decision = evaluate_running_restriction((
        SimpleNamespace(running_allowed=False, cross_training_allowed=True),
    ))

    assert decision.blocked is True
    assert decision.cross_training_allowed is True
    assert "interdit actuellement la course à pied" in decision.message
    assert "activité croisée peut être envisagée" in decision.message


def test_running_restriction_does_not_authorize_cross_training_by_default():
    decision = evaluate_running_restriction((
        SimpleNamespace(running_allowed=False, cross_training_allowed=False),
    ))

    assert decision.blocked is True
    assert decision.cross_training_allowed is False
    assert "ne peux pas non plus te proposer une activité croisée" in decision.message


def test_running_restriction_does_not_block_when_all_constraints_allow_running():
    decision = evaluate_running_restriction((
        SimpleNamespace(running_allowed=True, cross_training_allowed=True),
    ))

    assert decision.blocked is False
    assert decision.message is None
