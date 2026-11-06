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

    version = prescription.get("version")
    if version not in {1, 2}:
        raise TrainingSessionPrescriptionIntegrityError(
            "La version de prescription OpenCoach n'est pas prise en charge."
        )

    # Une séance de repos n'a pas nécessairement de bloc
    # de travail physiologique à analyser.
    if session.type == "rest":
        return

    blocks = prescription.get("blocks")
    if not isinstance(blocks, list):
        raise TrainingSessionPrescriptionIntegrityError(
            "La prescription doit conserver la liste ordonnée de ses phases."
        )

    if version == 2:
        allowed_phases = {
            "warmup", "main", "easy", "recovery",
            "cooldown", "technique", "strength", "transition",
        }
        for block in blocks:
            if not isinstance(block, dict):
                raise TrainingSessionPrescriptionIntegrityError(
                    "Chaque phase de la prescription doit être un objet structuré."
                )
            phase = block.get("phase")
            if phase is not None and phase not in allowed_phases:
                raise TrainingSessionPrescriptionIntegrityError(
                    f"Phase de séance non reconnue : {phase!r}."
                )
            block_intensity = block.get("intensity")
            if block_intensity is not None and (
                not isinstance(block_intensity, dict)
                or not isinstance(block_intensity.get("targets"), list)
                or not block_intensity["targets"]
            ):
                raise TrainingSessionPrescriptionIntegrityError(
                    "La cible d'intensité d'une phase doit contenir au moins une référence."
                )

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
