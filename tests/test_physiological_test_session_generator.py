import pytest

from opencoach.physiology.testing import (
    PhysiologicalTestSegmentIntensity,
    PhysiologicalTestSegmentType,
    PhysiologicalTestType,
    generate_physiological_test_session,
)


def test_half_cooper_contains_exact_six_minute_test() -> None:
    session = (
        generate_physiological_test_session(
            PhysiologicalTestType.HALF_COOPER
        )
    )

    test = session.analysis_segment

    assert (
        test.segment_type
        is PhysiologicalTestSegmentType.TEST
    )

    assert (
        test.intensity
        is PhysiologicalTestSegmentIntensity.MAXIMAL
    )

    assert (
        test.duration_seconds
        == 360
    )


def test_half_cooper_is_identifiable_in_metadata() -> None:
    session = (
        generate_physiological_test_session(
            PhysiologicalTestType.HALF_COOPER
        )
    )

    metadata = (
        session.metadata_dict()
    )

    assert (
        metadata["opencoach_session_kind"]
        == "physiological_test"
    )

    assert (
        metadata["test_protocol"]
        == "half_cooper"
    )

    assert (
        metadata[
            "expected_test_duration_seconds"
        ]
        == "360"
    )


def test_threshold_contains_twenty_minute_analysis_window() -> None:
    session = (
        generate_physiological_test_session(
            PhysiologicalTestType
            .THRESHOLD_20_MIN
        )
    )

    assert (
        session.analysis_segment.duration_seconds
        == 1200
    )

    assert (
        session.metadata_dict()[
            "test_protocol"
        ]
        == "threshold_20_min"
    )


def test_uphill_six_minute_test_has_trail_requirements() -> None:
    session = (
        generate_physiological_test_session(
            PhysiologicalTestType.UPHILL_6_MIN
        )
    )

    assert (
        session.analysis_segment.duration_seconds
        == 360
    )

    assert any(
        "Montée" in requirement
        or "montée" in requirement
        for requirement
        in session.terrain_requirements
    )


def test_all_sessions_have_one_analysis_window() -> None:
    protocols = (
        PhysiologicalTestType.HALF_COOPER,
        PhysiologicalTestType.THRESHOLD_20_MIN,
        PhysiologicalTestType.UPHILL_6_MIN,
    )

    for protocol in protocols:
        session = (
            generate_physiological_test_session(
                protocol
            )
        )

        windows = tuple(
            segment
            for segment in session.segments
            if segment.analysis_window
        )

        assert len(windows) == 1


def test_all_generated_tests_have_no_duplicate_metadata_keys() -> None:
    protocols = (
        PhysiologicalTestType.HALF_COOPER,
        PhysiologicalTestType.THRESHOLD_20_MIN,
        PhysiologicalTestType.UPHILL_6_MIN,
    )

    for protocol in protocols:
        session = (
            generate_physiological_test_session(
                protocol
            )
        )

        keys = tuple(
            key
            for key, _
            in session.metadata
        )

        assert len(keys) == len(
            set(keys)
        )


def test_unsupported_protocol_is_explicit() -> None:
    with pytest.raises(
        NotImplementedError
    ):
        generate_physiological_test_session(
            PhysiologicalTestType.VAMEVAL
        )
