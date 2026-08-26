from opencoach.planning.sessions.generators.catalog import (
    get_session_recipe,
    validate_session_recipe_catalog,
)
from opencoach.planning.sessions.prescription.physiological import (
    build_intensity_prescription,
    canonical_intensity_for_stimulus,
    validate_intensity_policy_catalog,
)
from opencoach.planning.stimulus.training import (
    StimulusLoadCategory,
    TrainingStimulus,
    stimulus_load_category,
)


def test_pre_race_activation_catalogs_are_complete() -> None:
    validate_session_recipe_catalog()
    validate_intensity_policy_catalog()


def test_pre_race_activation_is_low_load_support() -> None:
    stimulus = (
        TrainingStimulus.PRE_RACE_ACTIVATION
    )

    assert (
        stimulus_load_category(
            stimulus
        )
        is StimulusLoadCategory.SUPPORT
    )

    assert (
        canonical_intensity_for_stimulus(
            stimulus
        )
        == "easy"
    )


def test_pre_race_activation_has_specific_recipe() -> None:
    recipe = get_session_recipe(
        TrainingStimulus.PRE_RACE_ACTIVATION
    )

    assert (
        recipe.title
        == "Activation pré-course"
    )


def test_pre_race_activation_prescription_stays_controlled(
) -> None:
    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.PRE_RACE_ACTIVATION
            ),
            physiology=None,
        )
    )

    assert (
        prescription.primary_target.maximum
        <= 4
    )
