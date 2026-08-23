"""Moteur déterministe de trajectoire d'entraînement.

Le moteur transforme les événements connus par OpenCoach en adaptations
du cadre d'entraînement.

Il ne génère aucune séance concrète. Cette responsabilité appartient
au coach IA hebdomadaire.
"""

from __future__ import annotations

from opencoach.planning.trajectory.adjustment import (
    AdjustmentSeverity,
    LoadAdjustment,
    ProgressionAdjustment,
    TrajectoryAdjustment,
)
from opencoach.planning.trajectory.event import (
    EventImpact,
    RacePriority,
    TrajectoryEvent,
    TrajectoryEventType,
)


class CoachingTrajectoryEngine:
    """Interprète les événements affectant la trajectoire."""

    def adjust_for_event(
        self,
        event: TrajectoryEvent,
    ) -> TrajectoryAdjustment:
        """Produit l'adaptation correspondant à un événement."""

        if event.event_type is TrajectoryEventType.RACE:
            return self._adjust_for_race(event)

        if event.event_type is TrajectoryEventType.UNAVAILABILITY:
            return self._adjust_for_unavailability(event)

        if event.event_type is TrajectoryEventType.ILLNESS:
            return self._adjust_for_illness(event)

        if event.event_type is TrajectoryEventType.INJURY:
            return self._adjust_for_injury(event)

        if event.event_type is TrajectoryEventType.TRAINING_BREAK:
            return self._adjust_for_training_break(event)

        raise ValueError(
            f"Type d'événement non pris en charge : {event.event_type}"
        )

    def _adjust_for_race(
        self,
        event: TrajectoryEvent,
    ) -> TrajectoryAdjustment:
        if event.race_priority is RacePriority.A:
            return TrajectoryAdjustment(
                reason="Compétition objectif prioritaire.",
                severity=AdjustmentSeverity.MAJOR,
                load=LoadAdjustment.REDUCE,
                progression=ProgressionAdjustment.PAUSE,
                athlete_override_allowed=True,
                notes=(
                    "La trajectoire doit converger vers la course A.",
                    "Une récupération post-course devra être planifiée.",
                ),
            )

        if event.race_priority is RacePriority.B:
            return TrajectoryAdjustment(
                reason="Compétition intermédiaire importante.",
                severity=AdjustmentSeverity.MODERATE,
                load=LoadAdjustment.REDUCE_SLIGHTLY,
                progression=ProgressionAdjustment.CONTINUE,
                athlete_override_allowed=True,
                notes=(
                    "La course B s'intègre à la préparation principale.",
                    "Éviter un affûtage complet.",
                ),
            )

        return TrajectoryAdjustment(
            reason="Compétition secondaire ou préparatoire.",
            severity=AdjustmentSeverity.MINOR,
            load=LoadAdjustment.MAINTAIN,
            progression=ProgressionAdjustment.CONTINUE,
            athlete_override_allowed=True,
            notes=(
                "La course C peut être intégrée comme stimulus.",
            ),
        )

    def _adjust_for_unavailability(
        self,
        event: TrajectoryEvent,
    ) -> TrajectoryAdjustment:
        load = LoadAdjustment.MAINTAIN

        if event.impact in {
            EventImpact.HIGH,
            EventImpact.CRITICAL,
        }:
            load = LoadAdjustment.REDUCE

        return TrajectoryAdjustment(
            reason="Disponibilités d'entraînement contraintes.",
            severity=(
                AdjustmentSeverity.MODERATE
                if event.impact
                in {
                    EventImpact.HIGH,
                    EventImpact.CRITICAL,
                }
                else AdjustmentSeverity.MINOR
            ),
            load=load,
            progression=ProgressionAdjustment.CONTINUE,
            allow_schedule_compression=True,
            athlete_override_allowed=True,
            notes=(
                "Respecter les disponibilités réelles de l'athlète.",
                "Adapter l'enchaînement plutôt que refuser la semaine.",
            ),
        )

    def _adjust_for_illness(
        self,
        event: TrajectoryEvent,
    ) -> TrajectoryAdjustment:
        if event.impact is EventImpact.LOW:
            return TrajectoryAdjustment(
                reason="Maladie légère déclarée.",
                severity=AdjustmentSeverity.MODERATE,
                load=LoadAdjustment.REDUCE,
                progression=ProgressionAdjustment.SLOW,
                athlete_override_allowed=True,
            )

        return TrajectoryAdjustment(
            reason="Maladie affectant significativement l'entraînement.",
            severity=AdjustmentSeverity.MAJOR,
            load=LoadAdjustment.SUSPEND,
            progression=ProgressionAdjustment.PAUSE,
            requires_return_to_training=True,
            athlete_override_allowed=True,
        )

    def _adjust_for_injury(
        self,
        event: TrajectoryEvent,
    ) -> TrajectoryAdjustment:
        return TrajectoryAdjustment(
            reason="Blessure déclarée par l'athlète.",
            severity=(
                AdjustmentSeverity.MODERATE
                if event.impact is EventImpact.LOW
                else AdjustmentSeverity.MAJOR
            ),
            load=(
                LoadAdjustment.REDUCE
                if event.impact is EventImpact.LOW
                else LoadAdjustment.SUSPEND
            ),
            progression=ProgressionAdjustment.PAUSE,
            requires_return_to_training=True,
            athlete_override_allowed=True,
            notes=(
                "Les modalités réellement compatibles devront être "
                "déterminées séparément.",
            ),
        )

    def _adjust_for_training_break(
        self,
        event: TrajectoryEvent,
    ) -> TrajectoryAdjustment:
        duration_days = (
            event.end_date
            - event.start_date
        ).days + 1

        if duration_days <= 7:
            return TrajectoryAdjustment(
                reason="Interruption courte de l'entraînement.",
                severity=AdjustmentSeverity.MINOR,
                load=LoadAdjustment.REDUCE,
                progression=ProgressionAdjustment.SLOW,
                athlete_override_allowed=True,
            )

        return TrajectoryAdjustment(
            reason="Interruption prolongée de l'entraînement.",
            severity=AdjustmentSeverity.MAJOR,
            load=LoadAdjustment.REDUCE,
            progression=ProgressionAdjustment.REBUILD,
            requires_return_to_training=True,
            athlete_override_allowed=True,
        )
