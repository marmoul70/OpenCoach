"""Orchestration de la génération hebdomadaire OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.planning.physiology.snapshot import (
    PhysiologicalCalibrationSnapshot,
)
from opencoach.planning.sessions.coach_port import (
    SessionCoachPort,
    SessionCoachRequest,
)
from opencoach.planning.sessions.duration import (
    allocate_session_durations,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope import (
    WeeklyTrainingEnvelope,
)

from .models import (
    GeneratedTrainingSession,
    GeneratedTrainingWeek,
)


class WeeklyTrainingGenerationError(
    RuntimeError
):
    """Erreur métier pendant la génération hebdomadaire."""


@dataclass(slots=True)
class WeeklyTrainingGenerationService:
    """Transforme une enveloppe hebdomadaire en séances concrètes."""

    session_generator: SessionCoachPort

    def generate(
        self,
        *,
        envelope: WeeklyTrainingEnvelope,
        physiology: (
            PhysiologicalCalibrationSnapshot
            | None
        ) = None,
        athlete_context: str | None = None,
        additional_context: tuple[
            str,
            ...,
        ] = (),
    ) -> GeneratedTrainingWeek:
        """Génère toutes les séances de la semaine."""

        generated_sessions: list[
            GeneratedTrainingSession
        ] = []

        duration_allocations = (
            allocate_session_durations(
                slots=envelope.session_slots,
                target_load=(
                    envelope.target_load
                    or 0.0
                ),
                reference_weekly_duration_minutes=(
                    envelope.target_duration_minutes
                ),
                long_endurance_reference_minutes=(
                    envelope.long_endurance_reference_minutes
                ),
            )
        )

        duration_by_slot = {
            allocation.slot_id:
                allocation.duration_minutes
            for allocation
            in duration_allocations
        }

        for slot in envelope.session_slots:
            session_date = _resolve_slot_date(
                week_start=envelope.week_start,
                week_end=envelope.week_end,
                day=slot.day,
            )

            request = SessionCoachRequest(
                phase=envelope.phase,
                slot=slot,
                target_load=envelope.target_load,
                planned_duration_minutes=(
                    duration_by_slot[
                        slot.slot_id
                    ]
                ),
                phase_week_index=(
                    envelope.phase_week_index
                ),
                physiology=physiology,
                athlete_context=athlete_context,
                additional_context=(
                    additional_context
                ),
            )

            proposal = (
                self.session_generator
                .generate_session(
                    request=request,
                )
            )

            generated_sessions.append(
                GeneratedTrainingSession(
                    slot_id=slot.slot_id,
                    date=session_date,
                    day=slot.day,
                    phase=envelope.phase,
                    proposal=proposal,
                    vma_kmh=(
                        physiology.vma.value
                        if (
                            physiology is not None
                            and physiology.vma.usable
                            and physiology.vma.value
                            is not None
                            and physiology.vma.value > 0
                        )
                        else None
                    ),
                )
            )

        generated_sessions.sort(
            key=lambda session: (
                session.date,
                session.slot_id,
            )
        )

        return GeneratedTrainingWeek(
            week_start=envelope.week_start,
            week_end=envelope.week_end,
            phase=envelope.phase,
            sessions=tuple(
                generated_sessions
            ),
            target_load=envelope.target_load,
            notes=envelope.notes,
        )


def _resolve_slot_date(
    *,
    week_start: date,
    week_end: date,
    day: Weekday,
) -> date:
    """Convertit un Weekday en date réelle dans l'enveloppe."""

    target_weekday = _weekday_index(
        day
    )

    offset = (
        target_weekday
        - week_start.weekday()
    ) % 7

    target_date = (
        week_start
        + timedelta(
            days=offset
        )
    )

    if (
        target_date < week_start
        or target_date > week_end
    ):
        raise WeeklyTrainingGenerationError(
            (
                "Le jour "
                f"'{day.value}' ne correspond à aucune "
                "date de l'enveloppe hebdomadaire."
            )
        )

    return target_date


def _weekday_index(
    day: Weekday,
) -> int:
    mapping = {
        Weekday.MONDAY: 0,
        Weekday.TUESDAY: 1,
        Weekday.WEDNESDAY: 2,
        Weekday.THURSDAY: 3,
        Weekday.FRIDAY: 4,
        Weekday.SATURDAY: 5,
        Weekday.SUNDAY: 6,
    }

    return mapping[
        day
    ]
