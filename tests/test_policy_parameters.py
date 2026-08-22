import pytest

from opencoach.planning import (
    AbsoluteLoadLimitParameters,
    AssessmentTimingParameters,
    RaceProximityParameters,
    RecoverySpacingParameters,
    RelativeLoadLimitParameters,
    TaperParameters,
)


def test_relative_load_limit_accepts_valid_multiplier():
    parameters = RelativeLoadLimitParameters(
        reference="baseline",
        max_multiplier=1.15,
    )

    assert parameters.max_multiplier == 1.15


def test_relative_load_limit_rejects_non_positive_multiplier():
    with pytest.raises(
        ValueError,
        match="multiplicateur",
    ):
        RelativeLoadLimitParameters(
            reference="baseline",
            max_multiplier=0,
        )


def test_absolute_between_requires_upper_value():
    with pytest.raises(
        ValueError,
        match="borne supérieure",
    ):
        AbsoluteLoadLimitParameters(
            metric="distance_km",
            operator="between",
            value=30.0,
        )


def test_absolute_between_rejects_reversed_range():
    with pytest.raises(
        ValueError,
        match="supérieure",
    ):
        AbsoluteLoadLimitParameters(
            metric="distance_km",
            operator="between",
            value=50.0,
            upper_value=40.0,
        )


def test_absolute_single_comparison_rejects_upper_value():
    with pytest.raises(
        ValueError,
        match="between",
    ):
        AbsoluteLoadLimitParameters(
            metric="training_load",
            operator="lte",
            value=400.0,
            upper_value=450.0,
        )


def test_recovery_spacing_requires_positive_values():
    with pytest.raises(
        ValueError,
        match="build",
    ):
        RecoverySpacingParameters(
            max_build_weeks_before_recovery=0,
            minimum_recovery_days=5,
        )


def test_taper_parameters_accept_range():
    parameters = TaperParameters(
        minimum_days=7,
        maximum_days=21,
        minimum_load_ratio=0.4,
        maximum_load_ratio=0.8,
    )

    assert parameters.minimum_days == 7
    assert parameters.maximum_days == 21


def test_taper_rejects_invalid_duration_range():
    with pytest.raises(
        ValueError,
        match="durée maximale",
    ):
        TaperParameters(
            minimum_days=21,
            maximum_days=7,
            minimum_load_ratio=0.4,
            maximum_load_ratio=0.8,
        )


def test_taper_rejects_invalid_load_ratio():
    with pytest.raises(
        ValueError,
        match="ratio",
    ):
        TaperParameters(
            minimum_days=7,
            maximum_days=14,
            minimum_load_ratio=0.9,
            maximum_load_ratio=0.5,
        )


def test_race_proximity_accepts_zero_days():
    parameters = RaceProximityParameters(
        days_before_race=0,
    )

    assert parameters.days_before_race == 0


def test_assessment_timing_accepts_valid_delays():
    parameters = AssessmentTimingParameters(
        minimum_days_before_primary_race=14,
        minimum_days_between_assessments=21,
    )

    assert (
        parameters.minimum_days_between_assessments
        == 21
    )
