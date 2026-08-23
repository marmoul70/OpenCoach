from opencoach.planning.training_stimulus import (
    TrainingModality,
    TrainingStimulus,
)
from opencoach.planning.trajectory_adjustment import (
    AdjustmentSeverity,
    LoadAdjustment,
    ProgressionAdjustment,
    TrajectoryAdjustment,
)
from opencoach.planning.trajectory_adjustment_resolver import (
    resolve_trajectory_adjustments,
)


def create_adjustment(
    *,
    reason: str = "Test.",
    severity: AdjustmentSeverity = AdjustmentSeverity.MINOR,
    load: LoadAdjustment = LoadAdjustment.MAINTAIN,
    progression: ProgressionAdjustment = (
        ProgressionAdjustment.CONTINUE
    ),
    restricted_modalities: tuple[
        TrainingModality,
        ...
    ] = (),
    protected_stimuli: tuple[
        TrainingStimulus,
        ...
    ] = (),
    suppressed_stimuli: tuple[
        TrainingStimulus,
        ...
    ] = (),
    allow_schedule_compression: bool = True,
    requires_return_to_training: bool = False,
    athlete_override_allowed: bool = True,
) -> TrajectoryAdjustment:
    return TrajectoryAdjustment(
        reason=reason,
        severity=severity,
        load=load,
        progression=progression,
        restricted_modalities=restricted_modalities,
        protected_stimuli=protected_stimuli,
        suppressed_stimuli=suppressed_stimuli,
        allow_schedule_compression=allow_schedule_compression,
        requires_return_to_training=requires_return_to_training,
        athlete_override_allowed=athlete_override_allowed,
    )


def test_empty_adjustments_keep_normal_trajectory() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=()
    )

    assert result.load is LoadAdjustment.MAINTAIN

    assert (
        result.progression
        is ProgressionAdjustment.CONTINUE
    )

    assert result.allow_schedule_compression is True
    assert result.requires_return_to_training is False
    assert result.athlete_override_allowed is True


def test_strongest_load_adjustment_wins() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(
                load=LoadAdjustment.MAINTAIN,
            ),
            create_adjustment(
                load=LoadAdjustment.REDUCE,
            ),
            create_adjustment(
                load=LoadAdjustment.SUSPEND,
                progression=ProgressionAdjustment.PAUSE,
            ),
        )
    )

    assert result.load is LoadAdjustment.SUSPEND


def test_most_conservative_progression_wins() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(
                progression=ProgressionAdjustment.CONTINUE,
            ),
            create_adjustment(
                progression=ProgressionAdjustment.SLOW,
            ),
            create_adjustment(
                load=LoadAdjustment.SUSPEND,
                progression=ProgressionAdjustment.REBUILD,
                requires_return_to_training=True,
            ),
        )
    )

    assert (
        result.progression
        is ProgressionAdjustment.REBUILD
    )


def test_highest_severity_wins() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(
                severity=AdjustmentSeverity.MINOR,
            ),
            create_adjustment(
                severity=AdjustmentSeverity.MAJOR,
            ),
        )
    )

    assert result.severity is AdjustmentSeverity.MAJOR


def test_professional_maintain_cannot_cancel_injury_suspend() -> None:
    professional = create_adjustment(
        reason="Contrainte professionnelle.",
        load=LoadAdjustment.MAINTAIN,
        progression=ProgressionAdjustment.CONTINUE,
    )

    injury = create_adjustment(
        reason="Blessure.",
        severity=AdjustmentSeverity.MAJOR,
        load=LoadAdjustment.SUSPEND,
        progression=ProgressionAdjustment.REBUILD,
        requires_return_to_training=True,
        allow_schedule_compression=False,
    )

    result = resolve_trajectory_adjustments(
        adjustments=(
            professional,
            injury,
        )
    )

    assert result.load is LoadAdjustment.SUSPEND

    assert (
        result.progression
        is ProgressionAdjustment.REBUILD
    )

    assert result.requires_return_to_training is True


def test_schedule_compression_requires_all_adjustments_to_allow_it() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(
                allow_schedule_compression=True,
            ),
            create_adjustment(
                allow_schedule_compression=False,
            ),
        )
    )

    assert result.allow_schedule_compression is False


def test_return_to_training_is_preserved_if_any_adjustment_requires_it() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(),
            create_adjustment(
                load=LoadAdjustment.SUSPEND,
                progression=ProgressionAdjustment.REBUILD,
                requires_return_to_training=True,
            ),
        )
    )

    assert result.requires_return_to_training is True


def test_athlete_override_requires_all_adjustments_to_allow_it() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(
                athlete_override_allowed=True,
            ),
            create_adjustment(
                athlete_override_allowed=False,
            ),
        )
    )

    assert result.athlete_override_allowed is False


def test_restricted_modalities_are_merged_without_duplicates() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(
                restricted_modalities=(
                    TrainingModality.RUNNING,
                ),
            ),
            create_adjustment(
                restricted_modalities=(
                    TrainingModality.RUNNING,
                    TrainingModality.CYCLING,
                ),
            ),
        )
    )

    assert result.restricted_modalities == (
        TrainingModality.RUNNING,
        TrainingModality.CYCLING,
    )


def test_suppressed_stimulus_wins_over_protected_stimulus() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(
                protected_stimuli=(
                    TrainingStimulus.THRESHOLD,
                ),
            ),
            create_adjustment(
                suppressed_stimuli=(
                    TrainingStimulus.THRESHOLD,
                ),
            ),
        )
    )

    assert (
        TrainingStimulus.THRESHOLD
        not in result.protected_stimuli
    )

    assert (
        TrainingStimulus.THRESHOLD
        in result.suppressed_stimuli
    )


def test_reasons_are_preserved() -> None:
    result = resolve_trajectory_adjustments(
        adjustments=(
            create_adjustment(
                reason="Première raison.",
            ),
            create_adjustment(
                reason="Deuxième raison.",
            ),
        )
    )

    assert result.reasons == (
        "Première raison.",
        "Deuxième raison.",
    )
