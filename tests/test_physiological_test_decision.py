from datetime import date, timedelta
from uuid import uuid4

from opencoach.physiology.testing import (
    MeasurementConfidence,
    PhysiologicalMeasurementEvidence,
    PhysiologicalMetric,
    PhysiologicalTestDecision,
    PhysiologicalTestNeedRequest,
    PhysiologicalTestType,
    PreviousTestDecision,
    SportDiscipline,
    PhysiologicalTestAcquisitionMode,
    PhysiologicalTestingSeasonPhase,
    PhysiologicalTestNeedStatus,
    evaluate_physiological_test_need,
)


TODAY = date(
    2026,
    8,
    28,
)


RUNNING = (
    SportDiscipline.ROAD_RUNNING,
)


TRAIL = (
    SportDiscipline.ROAD_RUNNING,
    SportDiscipline.TRAIL_RUNNING,
)


def measurement(
    metric: PhysiologicalMetric,
    *,
    age_days: int,
    confidence: MeasurementConfidence = (
        MeasurementConfidence.HIGH
    ),
) -> PhysiologicalMeasurementEvidence:
    return PhysiologicalMeasurementEvidence(
        metric=metric,
        measured_at=(
            TODAY
            - timedelta(days=age_days)
        ),
        confidence=confidence,
        acquisition_mode=(
            PhysiologicalTestAcquisitionMode.SCHEDULED
        ),
    )


def request(
    metric: PhysiologicalMetric,
    *,
    measurement_value=...,
    phase=PhysiologicalTestingSeasonPhase.BUILD,
    disciplines=RUNNING,
    previous=None,
) -> PhysiologicalTestNeedRequest:
    if measurement_value is ...:
        measurement_value = None

    return PhysiologicalTestNeedRequest(
        metric=metric,
        reference_date=TODAY,
        disciplines=disciplines,
        season_phase=phase,
        measurement=measurement_value,
        previous_test_decision=previous,
    )


def test_recent_high_confidence_vma_needs_no_test() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                measurement_value=measurement(
                    PhysiologicalMetric.VMA,
                    age_days=20,
                ),
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.NOT_NEEDED
    )

    assert (
        decision.preferred_protocol
        is None
    )


def test_missing_vma_proposes_half_cooper() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.PROPOSE
    )

    assert (
        decision.preferred_protocol
        is PhysiologicalTestType.HALF_COOPER
    )


def test_stale_vma_proposes_test() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                measurement_value=measurement(
                    PhysiologicalMetric.VMA,
                    age_days=100,
                ),
            )
        )
    )

    assert decision.should_propose is True


def test_aging_vma_in_base_can_wait() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                measurement_value=measurement(
                    PhysiologicalMetric.VMA,
                    age_days=70,
                ),
                phase=PhysiologicalTestingSeasonPhase.BASE,
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.NOT_NEEDED
    )


def test_aging_vma_in_build_is_proposed() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                measurement_value=measurement(
                    PhysiologicalMetric.VMA,
                    age_days=70,
                ),
                phase=PhysiologicalTestingSeasonPhase.BUILD,
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.PROPOSE
    )


def test_threshold_defaults_to_20_min_not_30_min() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.THRESHOLD_HEART_RATE,
            )
        )
    )

    assert (
        decision.preferred_protocol
        is PhysiologicalTestType.THRESHOLD_20_MIN
    )


def test_recent_decline_defers_new_test() -> None:
    previous = PreviousTestDecision(
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        decision=(
            PhysiologicalTestDecision.DECLINED
        ),
        decided_at=(
            TODAY
            - timedelta(days=10)
        ),
    )

    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                previous=previous,
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.DEFER
    )


def test_old_decline_does_not_block_forever() -> None:
    previous = PreviousTestDecision(
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        decision=(
            PhysiologicalTestDecision.DECLINED
        ),
        decided_at=(
            TODAY
            - timedelta(days=40)
        ),
    )

    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                previous=previous,
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.PROPOSE
    )


def test_taper_defers_maximal_test() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                phase=PhysiologicalTestingSeasonPhase.TAPER,
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.DEFER
    )


def test_recovery_defers_test() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                phase=PhysiologicalTestingSeasonPhase.RECOVERY,
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.DEFER
    )


def test_return_to_training_defers_test() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                phase=(
                    PhysiologicalTestingSeasonPhase
                    .RETURN_TO_TRAINING
                ),
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.DEFER
    )


def test_low_confidence_recent_measurement_can_be_retested() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.VMA,
                measurement_value=measurement(
                    PhysiologicalMetric.VMA,
                    age_days=10,
                    confidence=(
                        MeasurementConfidence.LOW
                    ),
                ),
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.PROPOSE
    )


def test_trail_uphill_metric_uses_uphill_test() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.UPHILL_VAM,
                disciplines=TRAIL,
                phase=PhysiologicalTestingSeasonPhase.SPECIFIC,
            )
        )
    )

    assert (
        decision.preferred_protocol
        is PhysiologicalTestType.UPHILL_6_MIN
    )


def test_road_only_runner_does_not_get_trail_test() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.UPHILL_VAM,
                disciplines=RUNNING,
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.DEFER
    )

    assert (
        decision.preferred_protocol
        is None
    )


def test_max_hr_is_not_retested_after_100_days() -> None:
    decision = (
        evaluate_physiological_test_need(
            request(
                PhysiologicalMetric.MAX_HEART_RATE,
                measurement_value=measurement(
                    PhysiologicalMetric.MAX_HEART_RATE,
                    age_days=100,
                ),
            )
        )
    )

    assert (
        decision.status
        is PhysiologicalTestNeedStatus.NOT_NEEDED
    )
