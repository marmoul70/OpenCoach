from opencoach.coaching.recommendation_safety import (
    blocked_running_recommendation_message,
)


def test_running_recommendation_is_blocked_by_active_restriction():
    assert blocked_running_recommendation_message(
        {"blocked": True, "message": "Course interdite jusqu'à vendredi."}
    ) == "Course interdite jusqu'à vendredi."


def test_running_restriction_has_a_safe_fallback_message():
    message = blocked_running_recommendation_message({"blocked": True})
    assert message is not None
    assert "interdit la course à pied" in message


def test_missing_or_non_blocking_restriction_does_not_block_recommendation():
    assert blocked_running_recommendation_message(None) is None
    assert blocked_running_recommendation_message({"blocked": False}) is None
    assert blocked_running_recommendation_message({}) is None


def test_truthy_non_boolean_block_flag_is_not_treated_as_a_restriction():
    assert blocked_running_recommendation_message({"blocked": "true"}) is None
