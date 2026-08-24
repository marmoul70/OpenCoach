import pytest

from opencoach.planning.sessions.proposal import (
    SessionBlock,
    SessionProposal,
)
from opencoach.planning.stimulus.training import (
    TrainingModality,
    TrainingStimulus,
)
from opencoach.planning.sessions.prescription import (
    IntensityRange,
    IntensityReference,
    SessionIntensityPrescription,
    WorkStructure,
    WorkStructureType,
)

def create_proposal() -> SessionProposal:
    return SessionProposal(
        title="Sortie longue trail spécifique",
        modality=TrainingModality.RUNNING,
        duration_minutes=150,
        covered_stimuli=(
            TrainingStimulus.LONG_ENDURANCE,
        ),
        blocks=(
            SessionBlock(
                name="Échauffement",
                description=(
                    "Course facile sur terrain peu technique."
                ),
                duration_minutes=20,
            ),
            SessionBlock(
                name="Bloc principal",
                description=(
                    "Travail d'endurance longue "
                    "sur terrain vallonné."
                ),
                duration_minutes=115,
            ),
            SessionBlock(
                name="Retour au calme",
                description="Course très facile.",
                duration_minutes=15,
            ),
        ),
        objective=(
            "Développer l'endurance spécifique trail."
        ),
        coach_notes=(
            "Maintenir une intensité contrôlée.",
        ),
    )


def test_valid_session_proposal_is_created() -> None:
    proposal = create_proposal()

    assert (
        proposal.title
        == "Sortie longue trail spécifique"
    )

    assert proposal.duration_minutes == 150

    assert (
        proposal.modality
        is TrainingModality.RUNNING
    )

    assert len(proposal.blocks) == 3


def test_session_block_requires_name() -> None:
    with pytest.raises(
        ValueError,
        match="nom du bloc",
    ):
        SessionBlock(
            name="",
            description="Course facile.",
            duration_minutes=10,
        )


def test_session_block_requires_description() -> None:
    with pytest.raises(
        ValueError,
        match="description",
    ):
        SessionBlock(
            name="Échauffement",
            description="",
            duration_minutes=10,
        )


def test_session_block_rejects_invalid_duration() -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        SessionBlock(
            name="Échauffement",
            description="Course facile.",
            duration_minutes=0,
        )


def test_proposal_requires_title() -> None:
    with pytest.raises(
        ValueError,
        match="titre",
    ):
        SessionProposal(
            title="",
            modality=TrainingModality.RUNNING,
            duration_minutes=60,
            covered_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
            blocks=(
                SessionBlock(
                    name="Course",
                    description="Course facile.",
                    duration_minutes=60,
                ),
            ),
            objective="Endurance.",
        )


def test_proposal_requires_positive_duration() -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        SessionProposal(
            title="Course",
            modality=TrainingModality.RUNNING,
            duration_minutes=0,
            covered_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
            blocks=(
                SessionBlock(
                    name="Course",
                    description="Course facile.",
                ),
            ),
            objective="Endurance.",
        )


def test_proposal_requires_stimulus() -> None:
    with pytest.raises(
        ValueError,
        match="stimulus",
    ):
        SessionProposal(
            title="Course",
            modality=TrainingModality.RUNNING,
            duration_minutes=60,
            covered_stimuli=(),
            blocks=(
                SessionBlock(
                    name="Course",
                    description="Course facile.",
                    duration_minutes=60,
                ),
            ),
            objective="Endurance.",
        )


def test_proposal_requires_block() -> None:
    with pytest.raises(
        ValueError,
        match="bloc",
    ):
        SessionProposal(
            title="Course",
            modality=TrainingModality.RUNNING,
            duration_minutes=60,
            covered_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
            blocks=(),
            objective="Endurance.",
        )


def test_proposal_requires_objective() -> None:
    with pytest.raises(
        ValueError,
        match="objectif",
    ):
        SessionProposal(
            title="Course",
            modality=TrainingModality.RUNNING,
            duration_minutes=60,
            covered_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
            blocks=(
                SessionBlock(
                    name="Course",
                    description="Course facile.",
                    duration_minutes=60,
                ),
            ),
            objective="",
        )


def test_duplicate_stimuli_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="dupliqués",
    ):
        SessionProposal(
            title="Course facile",
            modality=TrainingModality.RUNNING,
            duration_minutes=60,
            covered_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
                TrainingStimulus.AEROBIC_EASY,
            ),
            blocks=(
                SessionBlock(
                    name="Course",
                    description="Course facile.",
                    duration_minutes=60,
                ),
            ),
            objective="Endurance.",
        )


def test_fully_timed_blocks_must_match_total_duration() -> None:
    with pytest.raises(
        ValueError,
        match="somme des durées",
    ):
        SessionProposal(
            title="Course",
            modality=TrainingModality.RUNNING,
            duration_minutes=60,
            covered_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
            blocks=(
                SessionBlock(
                    name="Échauffement",
                    description="Course facile.",
                    duration_minutes=10,
                ),
                SessionBlock(
                    name="Bloc principal",
                    description="Endurance.",
                    duration_minutes=40,
                ),
            ),
            objective="Endurance.",
        )


def test_partially_timed_blocks_are_allowed() -> None:
    proposal = SessionProposal(
        title="Trail vallonné",
        modality=TrainingModality.RUNNING,
        duration_minutes=90,
        covered_stimuli=(
            TrainingStimulus.AEROBIC_EASY,
        ),
        blocks=(
            SessionBlock(
                name="Échauffement",
                description="Course facile.",
                duration_minutes=15,
            ),
            SessionBlock(
                name="Terrain libre",
                description=(
                    "Poursuivre en endurance sur terrain vallonné."
                ),
            ),
        ),
        objective="Endurance générale.",
    )

    assert proposal.duration_minutes == 90

def test_proposal_rejects_intensity_for_uncovered_stimulus() -> None:
    prescription = (
        SessionIntensityPrescription(
            stimulus=TrainingStimulus.VO2MAX,
            primary_target=IntensityRange(
                reference=IntensityReference.RPE,
                minimum=8,
                maximum=9,
                unit="/10",
                label="RPE",
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="stimulus couvert",
    ):
        SessionProposal(
            title="Endurance facile",
            modality=TrainingModality.RUNNING,
            duration_minutes=45,
            covered_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
            blocks=(
                SessionBlock(
                    name="Endurance",
                    description="Course facile.",
                    duration_minutes=45,
                ),
            ),
            objective="Développer l'endurance.",
            intensity_prescription=(
                prescription
            ),
        )
def test_proposal_rejects_work_structure_for_uncovered_stimulus() -> None:
    structure = WorkStructure(
        structure_type=(
            WorkStructureType.CONTINUOUS
        ),
        stimulus=TrainingStimulus.VO2MAX,
        available_minutes=30,
        continuous_minutes=30,
        description="VO2max continu.",
    )

    with pytest.raises(
        ValueError,
        match="stimulus couvert",
    ):
        SessionProposal(
            title="Endurance facile",
            modality=TrainingModality.RUNNING,
            duration_minutes=45,
            covered_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
            blocks=(
                SessionBlock(
                    name="Endurance",
                    description="Course facile.",
                    duration_minutes=45,
                ),
            ),
            objective="Développer l'endurance.",
            work_structure=structure,
        )