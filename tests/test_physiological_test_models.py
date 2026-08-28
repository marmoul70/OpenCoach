import pytest

from opencoach.physiology.testing import (
    ActivityMetric,
    EvidenceLevel,
    PhysiologicalMetric,
    PhysiologicalTestProtocol,
    PhysiologicalTestType,
    SportDiscipline,
    PhysiologicalTestAcquisitionMode,
    PhysiologicalTestEffortLevel,
    PhysiologicalTestFatigueCost,
)


def create_protocol(
    **overrides,
) -> PhysiologicalTestProtocol:
    values = {
        "id": PhysiologicalTestType.HALF_COOPER,
        "name": "Test",
        "description": "Description",
        "disciplines": (
            SportDiscipline.ROAD_RUNNING,
        ),
        "target_metrics": (
            PhysiologicalMetric.VMA,
        ),
        "acquisition_modes": (
            PhysiologicalTestAcquisitionMode.SCHEDULED,
        ),
        "effort_level": PhysiologicalTestEffortLevel.MAXIMAL,
        "fatigue_cost": PhysiologicalTestFatigueCost.HIGH,
        "replaces_quality_session": True,
        "minimum_recovery_before_hours": 48,
        "minimum_recovery_after_hours": 48,
        "required_activity_metrics": (
            ActivityMetric.DURATION,
        ),
        "evidence_level": (
            EvidenceLevel.FIELD_STANDARD
        ),
        "instructions": (
            "Instruction.",
        ),
    }

    values.update(
        overrides
    )

    return PhysiologicalTestProtocol(
        **values
    )


def test_protocol_is_frozen() -> None:
    protocol = create_protocol()

    with pytest.raises(
        AttributeError
    ):
        protocol.name = "Autre"


def test_protocol_requires_name() -> None:
    with pytest.raises(
        ValueError
    ):
        create_protocol(
            name="   ",
        )


def test_protocol_requires_discipline() -> None:
    with pytest.raises(
        ValueError
    ):
        create_protocol(
            disciplines=(),
        )


def test_protocol_requires_target_metric() -> None:
    with pytest.raises(
        ValueError
    ):
        create_protocol(
            target_metrics=(),
        )


def test_protocol_requires_acquisition_mode() -> None:
    with pytest.raises(
        ValueError
    ):
        create_protocol(
            acquisition_modes=(),
        )


def test_recovery_cannot_be_negative() -> None:
    with pytest.raises(
        ValueError
    ):
        create_protocol(
            minimum_recovery_before_hours=-1,
        )
