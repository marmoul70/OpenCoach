import pytest

from opencoach.physiology.testing import (
    PhysiologicalTestSegmentIntensity,
    PhysiologicalTestSegmentType,
    PhysiologicalTestSession,
    PhysiologicalTestSessionSegment,
    PhysiologicalTestType,
)


def test_analysis_window_must_be_test_segment() -> None:
    with pytest.raises(
        ValueError
    ):
        PhysiologicalTestSessionSegment(
            segment_type=(
                PhysiologicalTestSegmentType.WARMUP
            ),
            title="Échauffement",
            instruction="Facile.",
            intensity=(
                PhysiologicalTestSegmentIntensity.EASY
            ),
            duration_seconds=600,
            analysis_window=True,
        )


def test_session_requires_exactly_one_analysis_window() -> None:
    segment = (
        PhysiologicalTestSessionSegment(
            segment_type=(
                PhysiologicalTestSegmentType.WARMUP
            ),
            title="Échauffement",
            instruction="Facile.",
            intensity=(
                PhysiologicalTestSegmentIntensity.EASY
            ),
            duration_seconds=600,
        )
    )

    with pytest.raises(
        ValueError
    ):
        PhysiologicalTestSession(
            protocol=(
                PhysiologicalTestType.HALF_COOPER
            ),
            title="Test",
            description="Description",
            segments=(segment,),
            terrain_requirements=(),
            execution_notes=(),
            expected_total_duration_minutes=20,
            metadata=(),
        )


def test_analysis_segment_property() -> None:
    warmup = (
        PhysiologicalTestSessionSegment(
            segment_type=(
                PhysiologicalTestSegmentType.WARMUP
            ),
            title="Warmup",
            instruction="Facile.",
            intensity=(
                PhysiologicalTestSegmentIntensity.EASY
            ),
            duration_seconds=600,
        )
    )

    test = (
        PhysiologicalTestSessionSegment(
            segment_type=(
                PhysiologicalTestSegmentType.TEST
            ),
            title="Test",
            instruction="Effort.",
            intensity=(
                PhysiologicalTestSegmentIntensity.MAXIMAL
            ),
            duration_seconds=360,
            analysis_window=True,
        )
    )

    session = PhysiologicalTestSession(
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        title="Test",
        description="Description",
        segments=(
            warmup,
            test,
        ),
        terrain_requirements=(),
        execution_notes=(),
        expected_total_duration_minutes=20,
        metadata=(
            (
                "test_protocol",
                "half_cooper",
            ),
        ),
    )

    assert (
        session.analysis_segment
        is test
    )

    assert (
        session.metadata_dict()[
            "test_protocol"
        ]
        == "half_cooper"
    )
