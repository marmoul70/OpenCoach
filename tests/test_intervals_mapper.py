from datetime import datetime, timezone

import pytest

from opencoach.integrations.intervals import (
    IntervalsDataError,
    map_intervals_activity,
)


def create_activity_data() -> dict:
    return {
        "id": "i176833761",
        "name": "Morning Course à pied",
        "type": "Run",
        "source": "SUUNTO",
        "external_id": "6a7ebece4c8dda52aa105ddf.fit",
        "start_date": "2026-08-14T06:01:34Z",
        "start_date_local": "2026-08-14T08:01:34",
        "device_name": "SUUNTO Suunto Race 2",
        "elapsed_time": 3866,
        "moving_time": 3834,
        "distance": 4453.0,
        "total_elevation_gain": 45.47586,
        "total_elevation_loss": 47.925415,
        "average_speed": 1.151,
        "max_speed": 1.59,
        "average_heartrate": 67,
        "max_heartrate": 80,
        "lthr": 172,
        "athlete_max_hr": 190,
        "average_cadence": 54.197704,
        "average_stride": 0.6428963,
        "average_stance_time": 411.6583,
        "average_vertical_oscillation": 44.68567,
        "icu_average_watts": None,
        "average_altitude": 305.36542,
        "min_altitude": 297.57642,
        "max_altitude": 316.9894,
        "average_temp": 30.61959,
        "min_temp": 27,
        "max_temp": 36,
        "calories": 275,
        "icu_training_load": 2,
        "icu_ctl": 18.286057,
        "icu_atl": 10.629515,
        "hr_load": 2,
        "icu_intensity": 13.648706,
    }


def test_intervals_activity_is_mapped_to_opencoach_activity() -> None:
    data = create_activity_data()

    activity = map_intervals_activity(data)

    assert activity.provider == "intervals"
    assert activity.provider_activity_id == "i176833761"

    assert activity.source == "SUUNTO"
    assert activity.source_file_name == (
        "6a7ebece4c8dda52aa105ddf.fit"
    )

    assert activity.name == "Morning Course à pied"
    assert activity.sport_type == "Run"

    assert activity.start_at == datetime(
        2026,
        8,
        14,
        6,
        1,
        34,
        tzinfo=timezone.utc,
    )

    assert activity.start_at_local == datetime(
        2026,
        8,
        14,
        8,
        1,
        34,
    )

    assert activity.device_name == "SUUNTO Suunto Race 2"

    assert activity.elapsed_time_seconds == 3866
    assert activity.moving_time_seconds == 3834

    assert activity.distance_m == 4453.0
    assert activity.elevation_gain_m == 45.47586
    assert activity.elevation_loss_m == 47.925415

    assert activity.average_speed_mps == 1.151
    assert activity.max_speed_mps == 1.59

    assert activity.average_heart_rate == 67
    assert activity.max_heart_rate == 80

    assert activity.lactate_threshold_heart_rate == 172
    assert activity.athlete_max_heart_rate == 190

    assert activity.average_cadence == 54.197704
    assert activity.average_stride_m == 0.6428963

    assert activity.training_load == 2
    assert activity.fitness_ctl == 18.286057
    assert activity.fatigue_atl == 10.629515
    assert activity.hr_load == 2
    assert activity.intensity == 13.648706


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "name",
        "type",
        "start_date",
    ],
)
def test_required_activity_fields_are_validated(
    field: str,
) -> None:
    data = create_activity_data()
    data[field] = None

    with pytest.raises(IntervalsDataError):
        map_intervals_activity(data)


def test_invalid_start_date_is_rejected() -> None:
    data = create_activity_data()
    data["start_date"] = "invalid"

    with pytest.raises(
        IntervalsDataError,
        match="Date Intervals.icu invalide",
    ):
        map_intervals_activity(data)