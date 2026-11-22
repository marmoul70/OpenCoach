"""Serialisation des réponses HTTP liées aux séances d'entraînement."""

from datetime import datetime, timezone

from opencoach.schemas.training_session import (
    SessionExecutionDebriefResponse,
    SessionExecutionMetricResponse,
    TrainingSessionResponse,
)


def to_response(
    session,
) -> TrainingSessionResponse:
    """Convertit une séance métier vers sa réponse API."""

    return TrainingSessionResponse(
        id=session.id,
        date=session.date,
        type=session.type,
        sport_type=session.sport_type,
        title=session.title,
        description=session.description,
        duration_minutes=session.duration_minutes,
        distance_km=session.distance_km,
        elevation_gain_m=session.elevation_gain_m,
        intensity=session.intensity,
        heart_rate_zone=session.heart_rate_zone,
        status=session.status,
        activity_id=session.activity_id,
        prescription=session.prescription,
        intervals_external_id=(
            session.intervals_external_id
        ),
        intervals_event_id=(
            session.intervals_event_id
        ),
        intervals_sync_status=(
            session.intervals_sync_status
        ),
        intervals_last_synced_at=(
            session.intervals_last_synced_at
        ),
        intervals_payload_hash=(
            session.intervals_payload_hash
        ),
        intervals_sync_error=(
            session.intervals_sync_error
        ),
        coros_sync_status=session.coros_sync_status,
        coros_scheduled_date=session.coros_scheduled_date,
        coros_sync_started_at=_as_utc(session.coros_sync_started_at),
        coros_last_synced_at=_as_utc(session.coros_last_synced_at),
        coros_sync_error=session.coros_sync_error,
    )




def _as_utc(value: datetime | None) -> datetime | None:
    """Expose les dates COROS en UTC explicite, même si SQLite les rend naïves."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _debrief_response(
    analysis,
) -> SessionExecutionDebriefResponse:
    """Convertit un débriefing persistant vers l'API."""

    return SessionExecutionDebriefResponse(
        id=analysis.id,
        training_session_id=(
            analysis.training_session_id
        ),
        activity_id=analysis.activity_id,
        goal_type=analysis.goal_type,
        overall_status=(
            analysis.overall_status
        ),
        technical_status=(
            analysis.technical_status
        ),
        objective=analysis.objective,
        metrics=[
            SessionExecutionMetricResponse(
                key=metric["key"],
                label=metric["label"],
                importance=(
                    metric["importance"]
                ),
                status=metric["status"],
                target_minimum=(
                    metric.get(
                        "target_minimum"
                    )
                ),
                target_maximum=(
                    metric.get(
                        "target_maximum"
                    )
                ),
                unit=metric.get("unit"),
                actual_value=(
                    metric.get(
                        "actual_value"
                    )
                ),
                delta=metric.get(
                    "delta"
                ),
                delta_percent=(
                    metric.get(
                        "delta_percent"
                    )
                ),
                message=metric.get(
                    "message"
                ),
            )
            for metric
            in analysis.metrics
        ],
        strengths=list(
            analysis.strengths
        ),
        attention_points=list(
            analysis.attention_points
        ),
        debriefing=analysis.debriefing,
        derived_results=[
            {
                "key": key,
                "value": value,
            }
            for key, value
            in analysis.derived_results
        ],
        analyzed_at=(
            analysis.analyzed_at
        ),
    )
