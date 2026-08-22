from opencoach.planning import (
    AssessmentNeed,
    consolidate_assessment_needs,
)


def create_need(
    *,
    assessment_type,
    metrics,
    priority="high",
):
    return AssessmentNeed(
        assessment_type=assessment_type,
        priority=priority,
        metrics=tuple(
            metrics
        ),
        reason="Calibration nécessaire.",
    )


def test_vameval_consolidates_vma_and_max_hr() -> None:
    needs = (
        create_need(
            assessment_type="vma_calibration",
            metrics=("vma",),
        ),
        create_need(
            assessment_type="max_heart_rate_calibration",
            metrics=("max_heart_rate",),
        ),
    )

    plans = consolidate_assessment_needs(
        needs
    )

    assert len(plans) == 1

    plan = plans[0]

    assert (
        plan.protocol.protocol_id
        == "vameval"
    )

    assert set(
        plan.assessment_types
    ) == {
        "vma_calibration",
        "max_heart_rate_calibration",
    }

    assert set(
        plan.covered_metrics
    ) == {
        "vma",
        "max_heart_rate",
    }


def test_half_cooper_can_also_cover_vma_and_max_hr() -> None:
    needs = (
        create_need(
            assessment_type="vma_calibration",
            metrics=("vma",),
        ),
        create_need(
            assessment_type="max_heart_rate_calibration",
            metrics=("max_heart_rate",),
        ),
    )

    plans = consolidate_assessment_needs(
        needs
    )

    assert len(plans) == 1

    assert plans[0].protocol.protocol_id in {
        "vameval",
        "half_cooper",
    }


def test_threshold_full_need_requires_full_protocol_coverage() -> None:
    needs = (
        create_need(
            assessment_type="threshold_calibration",
            metrics=(
                "threshold_heart_rate_1",
                "threshold_heart_rate_2",
            ),
        ),
    )

    plans = consolidate_assessment_needs(
        needs
    )

    assert len(plans) == 1

    assert (
        plans[0].protocol.protocol_id
        == "laboratory_threshold"
    )


def test_sv2_only_can_use_twenty_minute_test() -> None:
    needs = (
        create_need(
            assessment_type="threshold_calibration",
            metrics=(
                "threshold_heart_rate_2",
            ),
        ),
    )

    plans = consolidate_assessment_needs(
        needs
    )

    assert len(plans) == 1

    assert (
        plans[0].protocol.protocol_id
        == "twenty_minute_threshold"
    )


def test_highest_priority_is_preserved() -> None:
    needs = (
        create_need(
            assessment_type="vma_calibration",
            metrics=("vma",),
            priority="medium",
        ),
        create_need(
            assessment_type="max_heart_rate_calibration",
            metrics=("max_heart_rate",),
            priority="high",
        ),
    )

    plans = consolidate_assessment_needs(
        needs
    )

    assert len(plans) == 1

    assert plans[0].priority == "high"


def test_independent_needs_create_multiple_plans() -> None:
    needs = (
        create_need(
            assessment_type="vma_calibration",
            metrics=("vma",),
        ),
        create_need(
            assessment_type="threshold_calibration",
            metrics=(
                "threshold_heart_rate_1",
                "threshold_heart_rate_2",
            ),
        ),
    )

    plans = consolidate_assessment_needs(
        needs
    )

    assert len(plans) == 2

    protocol_ids = {
        plan.protocol.protocol_id
        for plan in plans
    }

    assert "laboratory_threshold" in (
        protocol_ids
    )

    assert (
        "vameval" in protocol_ids
        or "half_cooper" in protocol_ids
    )


def test_empty_needs_returns_empty_plans() -> None:
    assert consolidate_assessment_needs(
        ()
    ) == ()
