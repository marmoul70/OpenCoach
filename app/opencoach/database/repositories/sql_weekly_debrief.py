"""Implémentation SQLAlchemy du repository de débrief hebdomadaire."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.coaching.weekly_debrief import (
    WeeklyAdaptationDirection,
    WeeklyDebrief,
    WeeklyDebriefFacts,
    WeeklyDebriefVerdict,
)
from opencoach.database.models.weekly_debrief import (
    WeeklyDebriefRecord,
)
from opencoach.database.repositories.weekly_debrief import (
    StoredWeeklyDebrief,
    WeeklyDebriefAlreadyClosedError,
    WeeklyDebriefRepository,
    WeeklyDebriefRepositoryError,
)


def _to_storage_datetime(
    value: datetime,
) -> datetime:
    """Normalise un timestamp en UTC naïf pour SQLite."""

    if value.tzinfo is None:
        return value

    return (
        value.astimezone(timezone.utc)
        .replace(tzinfo=None)
    )


def _from_storage_datetime(
    value: datetime | None,
) -> datetime | None:
    """Expose toujours les timestamps persistés en UTC-aware."""

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


class SqlWeeklyDebriefRepository(
    WeeklyDebriefRepository,
):
    """Persistance SQL d'un bilan hebdomadaire clôturé."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_closed(
        self,
        athlete_profile_id: UUID,
        facts: WeeklyDebriefFacts,
        debrief: WeeklyDebrief,
        *,
        adaptation_payload: dict | None = None,
        allow_recalculation: bool = False,
    ) -> StoredWeeklyDebrief:
        """Crée le snapshot ou effectue un recalcul explicite."""

        self._validate_consistency(
            facts,
            debrief,
        )

        try:
            record = self._find(
                athlete_profile_id,
                facts.week_start,
            )

            now = _to_storage_datetime(
                datetime.now(
                    timezone.utc
                )
            )

            if (
                record is not None
                and not allow_recalculation
            ):
                raise WeeklyDebriefAlreadyClosedError(
                    "Le bilan de cette semaine "
                    "est déjà clôturé."
                )

            if record is None:
                record = WeeklyDebriefRecord(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    week_start=facts.week_start,
                    week_end=facts.week_end,
                    generated_at=now,
                )
                self.session.add(record)
            else:
                record.recalculated_at = now

            self._apply_snapshot(
                record,
                facts,
                debrief,
                adaptation_payload,
            )

            self.session.commit()
            self.session.refresh(record)

            return self._to_domain(record)

        except WeeklyDebriefAlreadyClosedError:
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WeeklyDebriefRepositoryError(
                "Impossible d'enregistrer "
                "le débrief hebdomadaire."
            ) from exc

    def get_for_week(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> StoredWeeklyDebrief | None:
        """Retourne le snapshot d'une semaine."""

        try:
            record = self._find(
                athlete_profile_id,
                week_start,
            )

            if record is None:
                return None

            return self._to_domain(record)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WeeklyDebriefRepositoryError(
                "Impossible de charger "
                "le débrief hebdomadaire."
            ) from exc

    def mark_planning_updated(
        self,
        athlete_profile_id: UUID,
        week_start: date,
        *,
        timestamp: datetime | None = None,
    ) -> StoredWeeklyDebrief | None:
        return self._mark_timestamp(
            athlete_profile_id,
            week_start,
            attribute="planning_updated_at",
            timestamp=timestamp,
        )

    def mark_notification_sent(
        self,
        athlete_profile_id: UUID,
        week_start: date,
        *,
        timestamp: datetime | None = None,
    ) -> StoredWeeklyDebrief | None:
        return self._mark_timestamp(
            athlete_profile_id,
            week_start,
            attribute="notification_sent_at",
            timestamp=timestamp,
        )

    def _mark_timestamp(
        self,
        athlete_profile_id: UUID,
        week_start: date,
        *,
        attribute: str,
        timestamp: datetime | None,
    ) -> StoredWeeklyDebrief | None:
        try:
            record = self._find(
                athlete_profile_id,
                week_start,
            )

            if record is None:
                return None

            value = (
                timestamp
                or datetime.now(
                    timezone.utc
                )
            )

            setattr(
                record,
                attribute,
                _to_storage_datetime(
                    value
                ),
            )

            self.session.commit()
            self.session.refresh(record)

            return self._to_domain(record)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WeeklyDebriefRepositoryError(
                "Impossible de mettre à jour "
                "les métadonnées du débrief."
            ) from exc

    def _find(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> WeeklyDebriefRecord | None:
        return self.session.scalar(
            select(
                WeeklyDebriefRecord
            ).where(
                WeeklyDebriefRecord.athlete_profile_id
                == athlete_profile_id,
                WeeklyDebriefRecord.week_start
                == week_start,
            )
        )

    @staticmethod
    def _validate_consistency(
        facts: WeeklyDebriefFacts,
        debrief: WeeklyDebrief,
    ) -> None:
        if (
            facts.week_start
            != debrief.week_start
            or facts.week_end
            != debrief.week_end
        ):
            raise ValueError(
                "Les dates du débrief ne correspondent "
                "pas aux faits consolidés."
            )

    @staticmethod
    def _facts_to_payload(
        facts: WeeklyDebriefFacts,
    ) -> dict:
        return {
            "planned_sessions": (
                facts.planned_sessions
            ),
            "completed_sessions": (
                facts.completed_sessions
            ),
            "skipped_sessions": (
                facts.skipped_sessions
            ),
            "supplementary_sessions": (
                facts.supplementary_sessions
            ),
            "planned_duration_minutes": (
                facts.planned_duration_minutes
            ),
            "actual_duration_minutes": (
                facts.actual_duration_minutes
            ),
            "planned_load": facts.planned_load,
            "actual_load": facts.actual_load,
            "key_sessions_planned": (
                facts.key_sessions_planned
            ),
            "key_sessions_completed": (
                facts.key_sessions_completed
            ),
            "compliant_intensity_sessions": (
                facts.compliant_intensity_sessions
            ),
            "analyzed_intensity_sessions": (
                facts.analyzed_intensity_sessions
            ),
            "history_confidence": (
                facts.history_confidence
            ),
        }

    @staticmethod
    def _facts_from_record(
        record: WeeklyDebriefRecord,
    ) -> WeeklyDebriefFacts:
        payload = record.facts_payload

        return WeeklyDebriefFacts(
            week_start=record.week_start,
            week_end=record.week_end,
            planned_sessions=(
                payload["planned_sessions"]
            ),
            completed_sessions=(
                payload["completed_sessions"]
            ),
            skipped_sessions=(
                payload["skipped_sessions"]
            ),
            supplementary_sessions=(
                payload["supplementary_sessions"]
            ),
            planned_duration_minutes=(
                payload["planned_duration_minutes"]
            ),
            actual_duration_minutes=(
                payload["actual_duration_minutes"]
            ),
            planned_load=payload["planned_load"],
            actual_load=payload["actual_load"],
            key_sessions_planned=(
                payload["key_sessions_planned"]
            ),
            key_sessions_completed=(
                payload["key_sessions_completed"]
            ),
            compliant_intensity_sessions=(
                payload[
                    "compliant_intensity_sessions"
                ]
            ),
            analyzed_intensity_sessions=(
                payload[
                    "analyzed_intensity_sessions"
                ]
            ),
            history_confidence=(
                payload["history_confidence"]
            ),
        )

    @classmethod
    def _apply_snapshot(
        cls,
        record: WeeklyDebriefRecord,
        facts: WeeklyDebriefFacts,
        debrief: WeeklyDebrief,
        adaptation_payload: dict | None,
    ) -> None:
        record.week_end = facts.week_end
        record.facts_payload = (
            cls._facts_to_payload(facts)
        )

        record.verdict = debrief.verdict.value
        record.adaptation_direction = (
            debrief.adaptation_direction.value
        )

        record.overall_score = (
            debrief.overall_score
        )
        record.adherence_score = (
            debrief.adherence_score
        )
        record.duration_score = (
            debrief.duration_score
        )
        record.load_score = (
            debrief.load_score
        )
        record.key_sessions_score = (
            debrief.key_sessions_score
        )
        record.intensity_score = (
            debrief.intensity_score
        )

        record.completion_ratio = (
            debrief.completion_ratio
        )
        record.duration_ratio = (
            debrief.duration_ratio
        )
        record.load_ratio = (
            debrief.load_ratio
        )

        record.headline = debrief.headline
        record.analysis = debrief.analysis

        record.strengths = list(
            debrief.strengths
        )
        record.warnings = list(
            debrief.warnings
        )

        record.adaptation_payload = (
            dict(adaptation_payload)
            if adaptation_payload is not None
            else None
        )

    @classmethod
    def _to_domain(
        cls,
        record: WeeklyDebriefRecord,
    ) -> StoredWeeklyDebrief:
        facts = cls._facts_from_record(
            record
        )

        debrief = WeeklyDebrief(
            week_start=record.week_start,
            week_end=record.week_end,
            verdict=WeeklyDebriefVerdict(
                record.verdict
            ),
            adaptation_direction=(
                WeeklyAdaptationDirection(
                    record.adaptation_direction
                )
            ),
            overall_score=record.overall_score,
            adherence_score=(
                record.adherence_score
            ),
            duration_score=(
                record.duration_score
            ),
            load_score=record.load_score,
            key_sessions_score=(
                record.key_sessions_score
            ),
            intensity_score=(
                record.intensity_score
            ),
            completion_ratio=(
                record.completion_ratio
            ),
            duration_ratio=(
                record.duration_ratio
            ),
            load_ratio=record.load_ratio,
            headline=record.headline,
            analysis=record.analysis,
            strengths=tuple(
                record.strengths
            ),
            warnings=tuple(
                record.warnings
            ),
        )

        return StoredWeeklyDebrief(
            id=record.id,
            athlete_profile_id=(
                record.athlete_profile_id
            ),
            facts=facts,
            debrief=debrief,
            adaptation_payload=(
                dict(record.adaptation_payload)
                if record.adaptation_payload
                is not None
                else None
            ),
            generated_at=(
                _from_storage_datetime(
                    record.generated_at
                )
            ),
            recalculated_at=(
                _from_storage_datetime(
                    record.recalculated_at
                )
            ),
            planning_updated_at=(
                _from_storage_datetime(
                    record.planning_updated_at
                )
            ),
            notification_sent_at=(
                _from_storage_datetime(
                    record.notification_sent_at
                )
            ),
        )
