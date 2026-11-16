from types import SimpleNamespace

from opencoach.coaching.assistant.execution_safety import (
    recommendation_execution_block_message,
)


def _result(tool, status="ok", data=None):
    return SimpleNamespace(tool=tool, status=status, data=data)


def test_non_recommendation_does_not_apply_recommendation_safeguards():
    assert recommendation_execution_block_message(False, []) is None


def test_recommendation_requires_constraints_and_recovery_results():
    message = recommendation_execution_block_message(
        True,
        [_result("active_constraints", data={}), _result("recovery_status", "failed")],
    )
    assert message is not None
    assert "ne peux donc pas te recommander" in message


def test_recommendation_is_blocked_by_coach_running_restriction():
    message = recommendation_execution_block_message(
        True,
        [
            _result("active_constraints", data={
                "running_restriction": {
                    "blocked": True,
                    "message": "Course interdite jusqu'à vendredi.",
                }
            }),
            _result("recovery_status", data={"available": True}),
        ],
    )
    assert message == "Course interdite jusqu'à vendredi."


def test_recommendation_can_proceed_when_coach_prerequisites_are_available():
    assert recommendation_execution_block_message(
        True,
        [
            _result("active_constraints", data={"running_restriction": {"blocked": False}}),
            _result("recovery_status", data={"available": True}),
        ],
    ) is None
