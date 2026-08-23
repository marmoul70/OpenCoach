import pytest

from opencoach.planning.stimulus.contextual_prescription import (
    ContextualStimulusPrescription,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.knowledge.race_demand_profile import (
    build_race_demand_profile,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.stimulus.weekly_demand import (
    StimulusDemand,
    StimulusDemandDensity,
    WeeklyStimulusDemand,
    build_weekly_stimulus_demand,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def create_requirement(
    *,
    stimulus: TrainingStimulus,
    priority: StimulusPriority,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=stimulus,
        priority=priority,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
    )


def create_prescription(
    *,
    phase: TrainingPhase = TrainingPhase.BUILD,
) -> ContextualStimulusPrescription:
    profile = build_race_demand_profile(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            priority=StimulusPriority.SUPPORT,
        ),
        create_requirement(
            stimulus=TrainingStimulus.THRESHOLD,
            priority=StimulusPriority.KEY,
        ),
        create_requirement(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            priority=StimulusPriority.KEY,
        ),
        create_requirement(
            stimulus=TrainingStimulus.STRENGTH_CORE,
            priority=StimulusPriority.SUPPORT,
        ),
        create_requirement(
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            priority=StimulusPriority.IMPORTANT,
        ),
    )

    return ContextualStimulusPrescription(
        phase=phase,
        race_profile=profile,
        requirements=requirements,
    )


def test_loading_week_requires_key_stimuli() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=500.0,
        reference_load=480.0,
    )

    threshold = result.demand_for(
        TrainingStimulus.THRESHOLD
    )

    long_endurance = result.demand_for(
        TrainingStimulus.LONG_ENDURANCE
    )

    assert threshold is not None
    assert long_endurance is not None

    assert threshold.minimum_occurrences == 1
    assert threshold.target_occurrences == 1

    assert long_endurance.minimum_occurrences == 1
    assert long_endurance.target_occurrences == 1


def test_loading_week_has_two_key_exposure_budget() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=500.0,
        reference_load=480.0,
    )

    assert result.maximum_key_exposures == 2


def test_aerobic_easy_can_repeat_on_normal_loading_week() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=500.0,
        reference_load=500.0,
    )

    easy = result.demand_for(
        TrainingStimulus.AEROBIC_EASY
    )

    assert easy is not None

    assert easy.minimum_occurrences == 0
    assert easy.target_occurrences == 2
    assert easy.maximum_occurrences == 3


def test_reduced_loading_week_reduces_easy_target() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=400.0,
        reference_load=500.0,
    )

    easy = result.demand_for(
        TrainingStimulus.AEROBIC_EASY
    )

    assert easy is not None

    assert easy.target_occurrences == 1


def test_loading_week_preserves_important_stimulus_as_desired() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=500.0,
        reference_load=500.0,
    )

    uphill = result.demand_for(
        TrainingStimulus.UPHILL_STRENGTH
    )

    assert uphill is not None

    assert uphill.minimum_occurrences == 0
    assert uphill.target_occurrences == 1
    assert uphill.maximum_occurrences == 1


def test_recovery_week_demotes_key_stimuli_from_required() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.RECOVERY,
        target_load=350.0,
        reference_load=500.0,
    )

    threshold = result.demand_for(
        TrainingStimulus.THRESHOLD
    )

    long_endurance = result.demand_for(
        TrainingStimulus.LONG_ENDURANCE
    )

    assert threshold is not None
    assert long_endurance is not None

    assert threshold.minimum_occurrences == 0
    assert threshold.target_occurrences == 0
    assert threshold.maximum_occurrences == 1

    assert long_endurance.minimum_occurrences == 0
    assert long_endurance.target_occurrences == 0
    assert long_endurance.maximum_occurrences == 1


def test_recovery_week_has_low_density() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.RECOVERY,
        target_load=350.0,
        reference_load=500.0,
    )

    assert (
        result.density
        is StimulusDemandDensity.LOW
    )

    assert result.maximum_key_exposures == 1


def test_recovery_keeps_easy_aerobic_present() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.RECOVERY,
        target_load=350.0,
        reference_load=500.0,
    )

    easy = result.demand_for(
        TrainingStimulus.AEROBIC_EASY
    )

    assert easy is not None

    assert easy.minimum_occurrences == 1
    assert easy.target_occurrences == 2


def test_taper_preserves_one_key_exposure() -> None:
    prescription = create_prescription(
        phase=TrainingPhase.TAPER,
    )

    result = build_weekly_stimulus_demand(
        prescription=prescription,
        week_type=TrajectoryWeekType.TAPER,
        target_load=300.0,
        reference_load=450.0,
    )

    threshold = result.demand_for(
        TrainingStimulus.THRESHOLD
    )

    assert threshold is not None

    assert threshold.minimum_occurrences == 1
    assert threshold.target_occurrences == 1

    assert result.maximum_key_exposures == 1


def test_return_to_training_disables_key_stimuli() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(
            phase=TrainingPhase.RETURN_TO_TRAINING,
        ),
        week_type=(
            TrajectoryWeekType.RETURN_TO_TRAINING
        ),
        target_load=250.0,
        reference_load=400.0,
    )

    threshold = result.demand_for(
        TrainingStimulus.THRESHOLD
    )

    assert threshold is not None

    assert threshold.minimum_occurrences == 0
    assert threshold.target_occurrences == 0
    assert threshold.maximum_occurrences == 0

    assert result.maximum_key_exposures == 0


def test_suspended_week_suppresses_all_stimuli() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.SUSPENDED,
        target_load=0.0,
        reference_load=500.0,
    )

    assert (
        result.density
        is StimulusDemandDensity.NONE
    )

    assert all(
        demand.suppressed
        for demand in result.demands
    )

    assert result.target_exposure_count == 0


def test_zero_load_suppresses_all_stimuli_even_on_loading_week() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=0.0,
        reference_load=500.0,
    )

    assert all(
        demand.maximum_occurrences == 0
        for demand in result.demands
    )


def test_load_ratio_is_exposed() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=450.0,
        reference_load=500.0,
    )

    assert result.load_ratio == pytest.approx(
        0.90
    )


def test_zero_reference_produces_unknown_load_ratio() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=100.0,
        reference_load=0.0,
    )

    assert result.load_ratio is None


def test_demand_for_unknown_stimulus_returns_none() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=500.0,
        reference_load=500.0,
    )

    assert (
        result.demand_for(
            TrainingStimulus.VO2MAX
        )
        is None
    )


def test_target_exposure_count_is_not_session_count() -> None:
    result = build_weekly_stimulus_demand(
        prescription=create_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=500.0,
        reference_load=500.0,
    )

    assert result.target_exposure_count > 0

    assert (
        result.target_exposure_count
        == sum(
            demand.target_occurrences
            for demand in result.demands
        )
    )


def test_stimulus_demand_rejects_negative_occurrences() -> None:
    requirement = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
    )

    with pytest.raises(
        ValueError,
        match="négatifs",
    ):
        StimulusDemand(
            requirement=requirement,
            minimum_occurrences=-1,
            target_occurrences=1,
            maximum_occurrences=2,
        )


def test_stimulus_demand_rejects_minimum_above_target() -> None:
    requirement = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
    )

    with pytest.raises(
        ValueError,
        match="minimum",
    ):
        StimulusDemand(
            requirement=requirement,
            minimum_occurrences=2,
            target_occurrences=1,
            maximum_occurrences=2,
        )


def test_stimulus_demand_rejects_target_above_maximum() -> None:
    requirement = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
    )

    with pytest.raises(
        ValueError,
        match="maximum",
    ):
        StimulusDemand(
            requirement=requirement,
            minimum_occurrences=0,
            target_occurrences=3,
            maximum_occurrences=2,
        )


def test_weekly_demand_rejects_negative_target_load() -> None:
    with pytest.raises(
        ValueError,
        match="cible",
    ):
        build_weekly_stimulus_demand(
            prescription=create_prescription(),
            week_type=TrajectoryWeekType.LOADING,
            target_load=-1.0,
            reference_load=500.0,
        )


def test_weekly_demand_rejects_negative_reference_load() -> None:
    with pytest.raises(
        ValueError,
        match="référence",
    ):
        build_weekly_stimulus_demand(
            prescription=create_prescription(),
            week_type=TrajectoryWeekType.LOADING,
            target_load=400.0,
            reference_load=-1.0,
        )


def test_duplicate_stimuli_are_rejected_by_weekly_demand() -> None:
    requirement = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
    )

    demand = StimulusDemand(
        requirement=requirement,
        minimum_occurrences=0,
        target_occurrences=1,
        maximum_occurrences=2,
    )

    with pytest.raises(
        ValueError,
        match="une seule fois",
    ):
        WeeklyStimulusDemand(
            phase=TrainingPhase.BASE,
            week_type=TrajectoryWeekType.LOADING,
            target_load=400.0,
            reference_load=400.0,
            load_ratio=1.0,
            density=StimulusDemandDensity.MODERATE,
            demands=(
                demand,
                demand,
            ),
            maximum_key_exposures=2,
        )
