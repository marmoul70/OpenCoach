"""Données détaillées d'une activité utiles au coach OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass


StreamValue = float | int | None


@dataclass(frozen=True, slots=True)
class ActivityInterval:
    """Intervalle observé dans une activité réalisée.

    Un intervalle fournisseur ne représente pas nécessairement
    une répétition prescrite. L'interprétation appartient au
    moteur d'analyse OpenCoach.
    """

    provider_interval_id: str | None

    interval_type: str | None
    label: str | None

    start_index: int
    end_index: int

    start_time_seconds: int
    end_time_seconds: int

    distance_m: float | None = None

    moving_time_seconds: int | None = None
    elapsed_time_seconds: int | None = None

    average_speed_mps: float | None = None

    average_heart_rate: float | None = None
    max_heart_rate: float | None = None

    average_cadence: float | None = None

    elevation_gain_m: float | None = None

    training_load: float | None = None

    def __post_init__(self) -> None:
        if self.start_index < 0:
            raise ValueError(
                "start_index ne peut pas être négatif."
            )

        if self.end_index < self.start_index:
            raise ValueError(
                "end_index ne peut pas être inférieur "
                "à start_index."
            )

        if self.start_time_seconds < 0:
            raise ValueError(
                "start_time_seconds ne peut pas "
                "être négatif."
            )

        if (
            self.end_time_seconds
            < self.start_time_seconds
        ):
            raise ValueError(
                "end_time_seconds ne peut pas être "
                "inférieur à start_time_seconds."
            )


@dataclass(frozen=True, slots=True)
class ActivityStream:
    """Série temporelle d'une métrique d'activité."""

    stream_type: str
    data: tuple[StreamValue, ...]

    def __post_init__(self) -> None:
        if not self.stream_type.strip():
            raise ValueError(
                "Le type de stream ne peut pas être vide."
            )


@dataclass(frozen=True, slots=True)
class ActivityStreams:
    """Streams utiles à l'analyse d'une activité."""

    time: ActivityStream | None = None
    distance: ActivityStream | None = None
    heartrate: ActivityStream | None = None
    velocity_smooth: ActivityStream | None = None
    cadence: ActivityStream | None = None
    watts: ActivityStream | None = None

    @property
    def available_types(self) -> tuple[str, ...]:
        values = []

        for stream in (
            self.time,
            self.distance,
            self.heartrate,
            self.velocity_smooth,
            self.cadence,
            self.watts,
        ):
            if stream is not None:
                values.append(
                    stream.stream_type
                )

        return tuple(values)


@dataclass(frozen=True, slots=True)
class ActivityDetail:
    """Données détaillées nécessaires au comparateur de séance."""

    provider_activity_id: str

    intervals: tuple[
        ActivityInterval,
        ...,
    ] = ()

    streams: ActivityStreams = ActivityStreams()

    interval_summary: tuple[str, ...] = ()
    provider_lap_count: int | None = None

    def __post_init__(self) -> None:
        if not self.provider_activity_id.strip():
            raise ValueError(
                "L'identifiant fournisseur de l'activité "
                "ne peut pas être vide."
            )
