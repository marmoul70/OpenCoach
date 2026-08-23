import pytest

from opencoach.planning.stimulus.training import (
    TrainingModality,
    TrainingStimulus,
)
from opencoach.planning.trajectory.adjustment import (
    AdjustmentSeverity,
    LoadAdjustment,
    ProgressionAdjustment,
    TrajectoryAdjustment,
)


def test_schedule_constraint_can_preserve_progression() -> None:
    adjustment = TrajectoryAdjustment(
        reason="Disponibilités professionnelles regroupées.",
        severity=AdjustmentSeverity.MINOR,
        load=LoadAdjustment.MAINTAIN,
        progression=ProgressionAdjustment.CONTINUE,
        allow_schedule_compression=True,
        athlete_override_allowed=True,
    )

    assert adjustment.allow_schedule_compression is True
    assert adjustment.athlete_override_allowed is True


def test_illness_can_pause_progression() -> None:
    adjustment = TrajectoryAdjustment(
        reason="Maladie temporaire.",
        severity=AdjustmentSeverity.MAJOR,
        load=LoadAdjustment.SUSPEND,
        progression=ProgressionAdjustment.PAUSE,
        athlete_override_allowed=True,
    )

    assert adjustment.load is LoadAdjustment.SUSPEND

    assert (
        adjustment.progression
        is ProgressionAdjustment.PAUSE
    )


def test_injury_can_restrict_running_without_removing_aerobic_work() -> None:
    adjustment = TrajectoryAdjustment(
        reason="Contrainte mécanique temporaire.",
        severity=AdjustmentSeverity.MAJOR,
        load=LoadAdjustment.REDUCE,
        progression=ProgressionAdjustment.SLOW,
        restricted_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.TRAIL_RUNNING,
        ),
        protected_stimuli=(
            TrainingStimulus.AEROBIC_EASY,
        ),
    )

    assert (
        TrainingModality.RUNNING
        in adjustment.restricted_modalities
    )

    assert (
        TrainingStimulus.AEROBIC_EASY
        in adjustment.protected_stimuli
    )


def test_return_to_training_can_rebuild_progression() -> None:
    adjustment = TrajectoryAdjustment(
        reason="Reprise après interruption.",
        severity=AdjustmentSeverity.MODERATE,
        load=LoadAdjustment.REDUCE,
        progression=ProgressionAdjustment.REBUILD,
        requires_return_to_training=True,
    )

    assert adjustment.requires_return_to_training is True


def test_rebuild_requires_return_to_training() -> None:
    with pytest.raises(
        ValueError,
        match="retour progressif",
    ):
        TrajectoryAdjustment(
            reason="Reconstruction invalide.",
            severity=AdjustmentSeverity.MODERATE,
            load=LoadAdjustment.REDUCE,
            progression=ProgressionAdjustment.REBUILD,
            requires_return_to_training=False,
        )


def test_stimulus_cannot_be_protected_and_suppressed() -> None:
    with pytest.raises(
        ValueError,
        match="simultanément",
    ):
        TrajectoryAdjustment(
            reason="Adaptation contradictoire.",
            severity=AdjustmentSeverity.MODERATE,
            load=LoadAdjustment.REDUCE,
            progression=ProgressionAdjustment.SLOW,
            protected_stimuli=(
                TrainingStimulus.THRESHOLD,
            ),
            suppressed_stimuli=(
                TrainingStimulus.THRESHOLD,
            ),
        )


def test_reason_cannot_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="raison",
    ):
        TrajectoryAdjustment(
            reason=" ",
            severity=AdjustmentSeverity.MINOR,
            load=LoadAdjustment.MAINTAIN,
            progression=ProgressionAdjustment.CONTINUE,
        )
