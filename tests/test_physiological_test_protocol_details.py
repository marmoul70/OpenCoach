from opencoach.physiology.testing.models import (
    PhysiologicalMetric,
    PhysiologicalTestType,
)
from opencoach.physiology.testing.protocol_details import (
    get_physiological_test_protocol_details,
    has_physiological_test_protocol_details,
)


def test_half_cooper_has_detailed_protocol() -> None:
    details = (
        get_physiological_test_protocol_details(
            PhysiologicalTestType.HALF_COOPER
        )
    )

    assert (
        details.protocol
        is PhysiologicalTestType.HALF_COOPER
    )

    assert (
        details.title
        == "Demi-Cooper"
    )

    assert (
        PhysiologicalMetric.VMA
        in details.target_metrics
    )


def test_half_cooper_contains_six_minute_effort() -> None:
    details = (
        get_physiological_test_protocol_details(
            PhysiologicalTestType.HALF_COOPER
        )
    )

    assert len(
        details.test_steps
    ) == 1

    effort = (
        details.test_steps[
            0
        ]
    )

    assert (
        effort.duration_minutes
        == 6
    )


def test_half_cooper_requires_distance_and_duration() -> None:
    details = (
        get_physiological_test_protocol_details(
            PhysiologicalTestType.HALF_COOPER
        )
    )

    assert (
        "distance"
        in details.required_activity_data
    )

    assert (
        "duration"
        in details.required_activity_data
    )


def test_half_cooper_declares_useful_debriefing_data() -> None:
    details = (
        get_physiological_test_protocol_details(
            PhysiologicalTestType.HALF_COOPER
        )
    )

    assert (
        "pace"
        in details.useful_activity_data
    )

    assert (
        "heart_rate"
        in details.useful_activity_data
    )

    assert (
        "elevation_gain"
        in details.useful_activity_data
    )

    assert (
        "laps"
        in details.useful_activity_data
    )


def test_half_cooper_defines_invalidation_rules() -> None:
    details = (
        get_physiological_test_protocol_details(
            PhysiologicalTestType.HALF_COOPER
        )
    )

    assert (
        len(
            details.invalidation_reasons
        )
        >= 4
    )


def test_half_cooper_details_are_registered() -> None:
    assert (
        has_physiological_test_protocol_details(
            PhysiologicalTestType.HALF_COOPER
        )
        is True
    )
