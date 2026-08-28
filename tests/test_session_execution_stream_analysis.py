import pytest

from opencoach.training.session_execution import (
    calculate_time_in_range,
)


def test_time_in_range_weights_real_time() -> None:
    result = calculate_time_in_range(
        time_values=(0, 1, 3, 6),
        metric_values=(140, 160, 140, 140),
        minimum=130,
        maximum=150,
    )

    assert result.valid_duration_seconds == 6.0
    assert result.in_range_duration_seconds == 4.0
    assert result.in_range_percent == 66.67


def test_missing_metric_sample_is_excluded() -> None:
    result = calculate_time_in_range(
        time_values=(0, 1, 3, 6),
        metric_values=(140, None, 140, 140),
        minimum=130,
        maximum=150,
    )

    assert result.valid_duration_seconds == 4.0
    assert result.in_range_duration_seconds == 4.0
    assert result.in_range_percent == 100.0


def test_non_increasing_time_is_ignored() -> None:
    result = calculate_time_in_range(
        time_values=(0, 2, 2, 5),
        metric_values=(140, 140, 160, 160),
        minimum=130,
        maximum=150,
    )

    assert result.valid_duration_seconds == 5.0
    assert result.in_range_duration_seconds == 2.0
    assert result.in_range_percent == 40.0


def test_stream_length_mismatch_uses_common_range() -> None:
    result = calculate_time_in_range(
        time_values=(0, 1, 2, 3, 4),
        metric_values=(140, 140, 160),
        minimum=130,
        maximum=150,
    )

    assert result.valid_duration_seconds == 2.0
    assert result.in_range_duration_seconds == 2.0
    assert result.in_range_percent == 100.0


def test_no_valid_duration_returns_no_percentage() -> None:
    result = calculate_time_in_range(
        time_values=(0,),
        metric_values=(140,),
        minimum=130,
        maximum=150,
    )

    assert result.valid_duration_seconds == 0.0
    assert result.in_range_percent is None
    assert result.has_data is False


def test_range_boundaries_are_inclusive() -> None:
    result = calculate_time_in_range(
        time_values=(0, 1, 2),
        metric_values=(130, 150, 170),
        minimum=130,
        maximum=150,
    )

    assert result.in_range_percent == 100.0


def test_invalid_range_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="borne maximale",
    ):
        calculate_time_in_range(
            time_values=(0, 1),
            metric_values=(140, 140),
            minimum=150,
            maximum=130,
        )
