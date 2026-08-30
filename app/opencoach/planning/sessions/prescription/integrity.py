"""Invariants des prescriptions de séances OpenCoach."""

from __future__ import annotations

from opencoach.models import TrainingSession


class TrainingSessionPrescriptionIntegrityError(
    ValueError
):
    """La prescription d'une séance coach est incohérente."""


def validate_training_session_prescription(
    session: TrainingSession,
) -> None:
    """Valide le contrat entre une séance coach et sa prescription.

    Une séance libre ou supplémentaire sans ``planning_key`` peut
    légitimement ne pas posséder de prescription structurée.

    En revanche, toute séance issue du planning OpenCoach doit
    conserver un contrat structuré cohérent avec son stimulus.
    """

    if session.planning_key is None:
        return

    prescription = session.prescription

    if not isinstance(
        prescription,
        dict,
    ):
        raise TrainingSessionPrescriptionIntegrityError(
            "Une séance générée par OpenCoach doit "
            "posséder une prescription structurée."
        )

    if prescription.get("version") != 1:
        raise TrainingSessionPrescriptionIntegrityError(
            "La prescription d'une séance OpenCoach "
            "doit utiliser la version 1."
        )

    # Une séance de repos n'a pas nécessairement de bloc
    # de travail physiologique à analyser.
    if session.type == "rest":
        return

    work_structure = prescription.get(
        "work_structure"
    )

    if not isinstance(
        work_structure,
        dict,
    ):
        raise TrainingSessionPrescriptionIntegrityError(
            "Une séance d'entraînement générée par "
            "OpenCoach doit posséder une structure "
            "de travail."
        )

    stimulus = work_structure.get(
        "stimulus"
    )

    if stimulus != session.type:
        raise TrainingSessionPrescriptionIntegrityError(
            "La prescription ne correspond plus au "
            "stimulus de la séance : "
            f"session={session.type!r}, "
            f"prescription={stimulus!r}."
        )

    intensity = prescription.get(
        "intensity"
    )

    if not isinstance(
        intensity,
        dict,
    ):
        raise TrainingSessionPrescriptionIntegrityError(
            "Une séance d'entraînement générée par "
            "OpenCoach doit posséder une prescription "
            "d'intensité."
        )

    targets = intensity.get(
        "targets"
    )

    if (
        not isinstance(
            targets,
            list,
        )
        or not targets
    ):
        raise TrainingSessionPrescriptionIntegrityError(
            "La prescription d'intensité doit contenir "
            "au moins une cible."
        )
