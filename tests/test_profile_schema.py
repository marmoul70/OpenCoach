import pytest

from opencoach.schemas.profile import (
    AthletePhysiologySchema,
    AthleteTrainingSchema,
)


def test_available_days_are_normalized_in_ascending_order() -> None:
    training = AthleteTrainingSchema(
        available_days=[5, 1, 3, 0],
    )

    assert training.available_days == [0, 1, 3, 5]


def test_available_days_reject_duplicates() -> None:
    with pytest.raises(ValueError, match="ne peuvent pas être dupliqués"):
        AthleteTrainingSchema(
            available_days=[1, 3, 3, 5],
        )


def test_physiology_accepts_valid_values() -> None:
    physiology = AthletePhysiologySchema(
        max_heart_rate=190,
        resting_heart_rate=50,
        threshold_heart_rate_1=145,
        threshold_heart_rate_2=165,
        vma=15.0,
    )

    assert physiology.max_heart_rate == 190
    assert physiology.resting_heart_rate == 50
    assert physiology.threshold_heart_rate_1 == 145
    assert physiology.threshold_heart_rate_2 == 165
    assert physiology.vma == 15.0


def test_physiology_rejects_resting_heart_rate_above_max() -> None:
    with pytest.raises(
        ValueError,
        match="FC au repos doit être inférieure à la FC maximale",
    ):
        AthletePhysiologySchema(
            resting_heart_rate=140,
            max_heart_rate=130,
        )


def test_physiology_rejects_resting_heart_rate_equal_to_max() -> None:
    with pytest.raises(
        ValueError,
        match="FC au repos doit être inférieure à la FC maximale",
    ):
        AthletePhysiologySchema(
            resting_heart_rate=130,
            max_heart_rate=130,
        )


def test_physiology_rejects_resting_heart_rate_above_sv1() -> None:
    with pytest.raises(
        ValueError,
        match="FC au repos doit être inférieure à SV1",
    ):
        AthletePhysiologySchema(
            resting_heart_rate=150,
            threshold_heart_rate_1=145,
        )


def test_physiology_rejects_resting_heart_rate_equal_to_sv1() -> None:
    with pytest.raises(
        ValueError,
        match="FC au repos doit être inférieure à SV1",
    ):
        AthletePhysiologySchema(
            resting_heart_rate=145,
            threshold_heart_rate_1=145,
        )


def test_physiology_rejects_sv1_above_sv2() -> None:
    with pytest.raises(
        ValueError,
        match="SV1 doit être inférieur à SV2",
    ):
        AthletePhysiologySchema(
            threshold_heart_rate_1=170,
            threshold_heart_rate_2=160,
        )


def test_physiology_rejects_sv1_equal_to_sv2() -> None:
    with pytest.raises(
        ValueError,
        match="SV1 doit être inférieur à SV2",
    ):
        AthletePhysiologySchema(
            threshold_heart_rate_1=160,
            threshold_heart_rate_2=160,
        )


def test_physiology_rejects_sv2_above_max() -> None:
    with pytest.raises(
        ValueError,
        match="SV2 doit être inférieur à la FC maximale",
    ):
        AthletePhysiologySchema(
            threshold_heart_rate_2=195,
            max_heart_rate=190,
        )


def test_physiology_rejects_sv2_equal_to_max() -> None:
    with pytest.raises(
        ValueError,
        match="SV2 doit être inférieur à la FC maximale",
    ):
        AthletePhysiologySchema(
            threshold_heart_rate_2=190,
            max_heart_rate=190,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_heart_rate", 251),
        ("resting_heart_rate", 151),
        ("threshold_heart_rate_1", 251),
        ("threshold_heart_rate_2", 251),
        ("vma", 40.1),
    ],
)
def test_physiology_rejects_values_above_allowed_limits(
    field: str,
    value: float,
) -> None:
    with pytest.raises(ValueError):
        AthletePhysiologySchema(**{field: value})


@pytest.mark.parametrize(
    "field",
    [
        "max_heart_rate",
        "resting_heart_rate",
        "threshold_heart_rate_1",
        "threshold_heart_rate_2",
        "vma",
    ],
)
def test_physiology_rejects_zero_values(field: str) -> None:
    with pytest.raises(ValueError):
        AthletePhysiologySchema(**{field: 0})