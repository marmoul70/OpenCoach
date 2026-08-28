"""Mapping des détails Intervals.icu vers le domaine OpenCoach."""

from __future__ import annotations

from opencoach.integrations.intervals.errors import (
    IntervalsDataError,
)
from opencoach.models import (
    ActivityDetail,
    ActivityInterval,
    ActivityStream,
    ActivityStreams,
)


SUPPORTED_STREAM_TYPES = {
    "time",
    "distance",
    "heartrate",
    "velocity_smooth",
    "cadence",
    "watts",
}


def map_intervals_activity_detail(
    detail_data: dict,
    stream_data: list[dict],
) -> ActivityDetail:
    """Convertit détail + streams Intervals en modèle OpenCoach."""

    provider_activity_id = _required_string(
        detail_data,
        "id",
    )

    intervals = _map_intervals(
        detail_data.get(
            "icu_intervals"
        ),
    )

    streams = _map_streams(
        stream_data,
    )

    interval_summary = _map_interval_summary(
        detail_data.get(
            "interval_summary"
        )
    )

    lap_count = detail_data.get(
        "icu_lap_count"
    )

    if (
        lap_count is not None
        and not isinstance(lap_count, int)
    ):
        raise IntervalsDataError(
            "icu_lap_count Intervals.icu invalide."
        )

    return ActivityDetail(
        provider_activity_id=provider_activity_id,
        intervals=intervals,
        streams=streams,
        interval_summary=interval_summary,
        provider_lap_count=lap_count,
    )


def _map_intervals(
    raw_intervals: object,
) -> tuple[ActivityInterval, ...]:
    if raw_intervals is None:
        return ()

    if not isinstance(
        raw_intervals,
        list,
    ):
        raise IntervalsDataError(
            "icu_intervals Intervals.icu invalide."
        )

    result: list[ActivityInterval] = []

    for raw in raw_intervals:
        if not isinstance(
            raw,
            dict,
        ):
            raise IntervalsDataError(
                "Intervalle Intervals.icu invalide."
            )

        start_index = _required_int(
            raw,
            "start_index",
        )
        end_index = _required_int(
            raw,
            "end_index",
        )
        start_time = _required_int(
            raw,
            "start_time",
        )
        end_time = _required_int(
            raw,
            "end_time",
        )

        provider_interval_id = raw.get(
            "id"
        )

        if provider_interval_id is not None:
            provider_interval_id = str(
                provider_interval_id
            )

        result.append(
            ActivityInterval(
                provider_interval_id=(
                    provider_interval_id
                ),
                interval_type=_optional_string(
                    raw.get("type")
                ),
                label=_optional_string(
                    raw.get("label")
                ),
                start_index=start_index,
                end_index=end_index,
                start_time_seconds=start_time,
                end_time_seconds=end_time,
                distance_m=_optional_number(
                    raw.get("distance")
                ),
                moving_time_seconds=(
                    _optional_int(
                        raw.get("moving_time")
                    )
                ),
                elapsed_time_seconds=(
                    _optional_int(
                        raw.get("elapsed_time")
                    )
                ),
                average_speed_mps=(
                    _optional_number(
                        raw.get("average_speed")
                    )
                ),
                average_heart_rate=(
                    _optional_number(
                        raw.get(
                            "average_heartrate"
                        )
                    )
                ),
                max_heart_rate=(
                    _optional_number(
                        raw.get(
                            "max_heartrate"
                        )
                    )
                ),
                average_cadence=(
                    _optional_number(
                        raw.get(
                            "average_cadence"
                        )
                    )
                ),
                elevation_gain_m=(
                    _optional_number(
                        raw.get(
                            "total_elevation_gain"
                        )
                    )
                ),
                training_load=(
                    _optional_number(
                        raw.get(
                            "training_load"
                        )
                    )
                ),
            )
        )

    return tuple(result)


def _map_streams(
    raw_streams: object,
) -> ActivityStreams:
    if not isinstance(
        raw_streams,
        list,
    ):
        raise IntervalsDataError(
            "Streams Intervals.icu invalides."
        )

    mapped: dict[str, ActivityStream] = {}

    for raw in raw_streams:
        if not isinstance(
            raw,
            dict,
        ):
            raise IntervalsDataError(
                "Stream Intervals.icu invalide."
            )

        stream_type = raw.get(
            "type"
        )

        if not isinstance(
            stream_type,
            str,
        ):
            raise IntervalsDataError(
                "Type de stream Intervals.icu invalide."
            )

        if (
            stream_type
            not in SUPPORTED_STREAM_TYPES
        ):
            continue

        data = raw.get(
            "data"
        )

        if not isinstance(
            data,
            list,
        ):
            raise IntervalsDataError(
                f"Données du stream {stream_type!r} "
                "invalides."
            )

        values = tuple(
            _stream_value(
                value,
                stream_type=stream_type,
            )
            for value in data
        )

        mapped[stream_type] = ActivityStream(
            stream_type=stream_type,
            data=values,
        )

    return ActivityStreams(
        time=mapped.get("time"),
        distance=mapped.get("distance"),
        heartrate=mapped.get("heartrate"),
        velocity_smooth=mapped.get(
            "velocity_smooth"
        ),
        cadence=mapped.get("cadence"),
        watts=mapped.get("watts"),
    )


def _map_interval_summary(
    value: object,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if not isinstance(
        value,
        list,
    ):
        raise IntervalsDataError(
            "interval_summary Intervals.icu invalide."
        )

    result: list[str] = []

    for item in value:
        if not isinstance(
            item,
            str,
        ):
            raise IntervalsDataError(
                "Entrée interval_summary invalide."
            )

        result.append(
            item
        )

    return tuple(result)


def _required_string(
    data: dict,
    field: str,
) -> str:
    value = data.get(field)

    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise IntervalsDataError(
            f"Champ Intervals.icu obligatoire absent : "
            f"{field}."
        )

    return value.strip()


def _required_int(
    data: dict,
    field: str,
) -> int:
    value = data.get(field)

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
    ):
        raise IntervalsDataError(
            f"Champ Intervals.icu entier invalide : "
            f"{field}."
        )

    return value


def _optional_int(
    value: object,
) -> int | None:
    if value is None:
        return None

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
    ):
        raise IntervalsDataError(
            "Valeur entière Intervals.icu invalide."
        )

    return value


def _optional_number(
    value: object,
) -> float | None:
    if value is None:
        return None

    if (
        not isinstance(
            value,
            (int, float),
        )
        or isinstance(value, bool)
    ):
        raise IntervalsDataError(
            "Valeur numérique Intervals.icu invalide."
        )

    return float(value)


def _optional_string(
    value: object,
) -> str | None:
    if value is None:
        return None

    if not isinstance(
        value,
        str,
    ):
        raise IntervalsDataError(
            "Valeur texte Intervals.icu invalide."
        )

    stripped = value.strip()

    return stripped or None


def _stream_value(
    value: object,
    *,
    stream_type: str,
) -> float | int | None:
    if value is None:
        return None

    if (
        not isinstance(
            value,
            (int, float),
        )
        or isinstance(value, bool)
    ):
        raise IntervalsDataError(
            f"Valeur invalide dans le stream "
            f"{stream_type!r}."
        )

    return value
