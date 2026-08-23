from opencoach.planning.return_to_training_clearance import (
    ReadinessAnswer,
    ReturnToTrainingReadiness,
    evaluate_return_to_training_clearance,
)


def create_ready_state() -> ReturnToTrainingReadiness:
    return ReturnToTrainingReadiness(
        blocking_symptoms=ReadinessAnswer.NO,
        recovery_sufficient=ReadinessAnswer.YES,
        clearance_confirmed=ReadinessAnswer.YES,
    )


def test_clearance_is_allowed_when_all_conditions_are_met() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=False,
        readiness=create_ready_state(),
    )

    assert result.allowed is True
    assert result.reasons == ()


def test_minimum_period_cannot_be_bypassed() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=False,
        requires_clearance=False,
        readiness=create_ready_state(),
    )

    assert result.allowed is False

    assert any(
        "durée minimale" in reason
        for reason in result.reasons
    )


def test_blocking_symptoms_prevent_clearance() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=False,
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.YES,
            recovery_sufficient=ReadinessAnswer.YES,
            clearance_confirmed=ReadinessAnswer.YES,
        ),
    )

    assert result.allowed is False

    assert any(
        "symptômes bloquants" in reason
        for reason in result.reasons
    )


def test_insufficient_recovery_prevents_clearance() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=False,
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.NO,
            recovery_sufficient=ReadinessAnswer.NO,
            clearance_confirmed=ReadinessAnswer.YES,
        ),
    )

    assert result.allowed is False

    assert any(
        "récupération" in reason
        for reason in result.reasons
    )


def test_required_clearance_must_be_confirmed() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=True,
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.NO,
            recovery_sufficient=ReadinessAnswer.YES,
            clearance_confirmed=ReadinessAnswer.NO,
        ),
    )

    assert result.allowed is False

    assert any(
        "n'est pas confirmée" in reason
        for reason in result.reasons
    )


def test_confirmation_is_not_required_when_policy_does_not_require_it() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=False,
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.NO,
            recovery_sufficient=ReadinessAnswer.YES,
            clearance_confirmed=ReadinessAnswer.NO,
        ),
    )

    assert result.allowed is True


def test_unknown_readiness_does_not_allow_clearance() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=False,
        readiness=ReturnToTrainingReadiness(),
    )

    assert result.allowed is False

    assert any(
        "pas renseigné" in reason
        for reason in result.reasons
    )


def test_unknown_symptoms_prevent_clearance() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=False,
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.UNKNOWN,
            recovery_sufficient=ReadinessAnswer.YES,
            clearance_confirmed=ReadinessAnswer.YES,
        ),
    )

    assert result.allowed is False

    assert any(
        "symptômes" in reason
        and "pas renseigné" in reason
        for reason in result.reasons
    )


def test_unknown_recovery_prevents_clearance() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=False,
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.NO,
            recovery_sufficient=ReadinessAnswer.UNKNOWN,
            clearance_confirmed=ReadinessAnswer.YES,
        ),
    )

    assert result.allowed is False

    assert any(
        "récupération" in reason
        and "pas renseigné" in reason
        for reason in result.reasons
    )


def test_unknown_required_clearance_prevents_clearance() -> None:
    result = evaluate_return_to_training_clearance(
        minimum_completed=True,
        requires_clearance=True,
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.NO,
            recovery_sufficient=ReadinessAnswer.YES,
            clearance_confirmed=ReadinessAnswer.UNKNOWN,
        ),
    )

    assert result.allowed is False

    assert any(
        "validation" in reason
        and "pas renseignée" in reason
        for reason in result.reasons
    )