"""Invariants des prescriptions de séances OpenCoach."""

from __future__ import annotations

from opencoach.models import TrainingSession


class TrainingSessionPrescriptionIntegrityError(
    ValueError
):
    """La prescription d'une séance coach est incohérente."""


def _validate_intensity_targets(
    intensity: dict,
    *,
    context: str,
) -> None:
    targets = intensity.get("targets")
    if not isinstance(targets, list) or not targets:
        raise TrainingSessionPrescriptionIntegrityError(
            f"La prescription d'intensité {context} est vide."
        )
    for target in targets:
        if not isinstance(target, dict):
            raise TrainingSessionPrescriptionIntegrityError(
                f"Une cible d'intensité {context} est invalide."
            )
        reference = target.get("reference")
        if not isinstance(reference, str) or not reference.strip():
            raise TrainingSessionPrescriptionIntegrityError(
                f"Une référence d'intensité {context} est absente."
            )
        minimum = target.get("minimum")
        maximum = target.get("maximum")
        if (
            isinstance(minimum, bool)
            or isinstance(maximum, bool)
            or not isinstance(minimum, (int, float))
            or not isinstance(maximum, (int, float))
            or minimum < 0
            or maximum < minimum
        ):
            raise TrainingSessionPrescriptionIntegrityError(
                f"Les bornes d'intensité {context} sont invalides."
            )


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
    if (
        isinstance(version, bool)
        or not isinstance(version, int)
        or version not in {1, 2}
    ):
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
        if not blocks:
            raise TrainingSessionPrescriptionIntegrityError(
                "Une prescription version 2 doit contenir au moins une phase."
            )

        total_duration = 0
        all_blocks_timed = True

        for block in blocks:
            if not isinstance(block, dict):
                raise TrainingSessionPrescriptionIntegrityError(
                    "Chaque phase de la prescription doit être un objet structuré."
                )

            name = block.get("name")
            description = block.get("description")
            if not isinstance(name, str) or not name.strip():
                raise TrainingSessionPrescriptionIntegrityError(
                    "Chaque phase doit posséder un nom explicite."
                )
            if not isinstance(description, str) or not description.strip():
                raise TrainingSessionPrescriptionIntegrityError(
                    "Chaque phase doit conserver ses consignes."
                )

            phase = block.get("phase")
            if phase not in allowed_phases:
                raise TrainingSessionPrescriptionIntegrityError(
                    f"Phase de séance absente ou non reconnue : {phase!r}."
                )

            duration = block.get("duration_minutes")
            if duration is None:
                all_blocks_timed = False
            elif (
                isinstance(duration, bool)
                or not isinstance(duration, int)
                or duration <= 0
            ):
                raise TrainingSessionPrescriptionIntegrityError(
                    "La durée de chaque phase doit être un entier strictement positif."
                )
            else:
                total_duration += duration

            for target_key in (
                "target_distance_meters",
                "target_elevation_gain_meters",
                "target_duration_seconds",
            ):
                target_value = block.get(target_key)
                if target_value is not None and (
                    isinstance(target_value, bool)
                    or not isinstance(target_value, int)
                    or target_value <= 0
                ):
                    raise TrainingSessionPrescriptionIntegrityError(
                        f"La cible {target_key} doit être un entier strictement positif."
                    )

            block_intensity = block.get("intensity")
            if (
                not isinstance(block_intensity, dict)
                or not isinstance(block_intensity.get("targets"), list)
                or not block_intensity["targets"]
            ):
                raise TrainingSessionPrescriptionIntegrityError(
                    "Chaque phase doit conserver au moins une cible ou consigne d'intensité."
                )
            _validate_intensity_targets(
                block_intensity,
                context="d'une phase",
            )

        if all_blocks_timed and total_duration != session.duration_minutes:
            raise TrainingSessionPrescriptionIntegrityError(
                "La somme des durées des phases ne correspond pas à la durée totale de la séance."
            )

        recovery_intensity = prescription.get("recovery_intensity")
        if recovery_intensity is not None:
            if (
                not isinstance(recovery_intensity, dict)
                or not isinstance(recovery_intensity.get("targets"), list)
                or not recovery_intensity["targets"]
            ):
                raise TrainingSessionPrescriptionIntegrityError(
                    "La prescription de récupération doit contenir au moins une cible."
                )
            _validate_intensity_targets(
                recovery_intensity,
                context="des récupérations",
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

    if version == 2:
        structure_type = work_structure.get("type")
        if structure_type not in {
            "continuous", "intervals", "repeats",
            "technical", "strength", "circuit",
        }:
            raise TrainingSessionPrescriptionIntegrityError(
                "Le type de structure de travail est absent ou non reconnu."
            )

        intervals = work_structure.get("intervals")
        if not isinstance(intervals, list):
            raise TrainingSessionPrescriptionIntegrityError(
                "La structure version 2 doit conserver sa liste d'intervalles."
            )
        if structure_type == "continuous":
            continuous_minutes = work_structure.get("continuous_minutes")
            if (
                isinstance(continuous_minutes, bool)
                or not isinstance(continuous_minutes, int)
                or continuous_minutes <= 0
            ):
                raise TrainingSessionPrescriptionIntegrityError(
                    "Une séance continue doit définir une durée positive."
                )
        if structure_type in {"intervals", "repeats"} and not intervals:
            raise TrainingSessionPrescriptionIntegrityError(
                "Une séance fractionnée doit contenir au moins une série."
            )
        if isinstance(intervals, list):
            for interval in intervals:
                if not isinstance(interval, dict):
                    raise TrainingSessionPrescriptionIntegrityError(
                        "Chaque série doit être un objet structuré."
                    )

                repetitions = interval.get("repetitions")
                if (
                    isinstance(repetitions, bool)
                    or not isinstance(repetitions, int)
                    or repetitions <= 0
                ):
                    raise TrainingSessionPrescriptionIntegrityError(
                        "Chaque série doit posséder un nombre de répétitions positif."
                    )

                work_duration = interval.get("work_duration")
                work_unit = interval.get("work_unit")
                work_distance = interval.get("work_distance_meters")
                if work_duration is None and work_unit is not None:
                    raise TrainingSessionPrescriptionIntegrityError(
                        "Une unité de travail ne peut pas exister sans durée."
                    )
                if work_duration is not None and (
                    isinstance(work_duration, bool)
                    or not isinstance(work_duration, int)
                    or work_duration <= 0
                    or work_unit not in {"seconds", "minutes"}
                ):
                    raise TrainingSessionPrescriptionIntegrityError(
                        "La durée ou l'unité de travail d'une série est invalide."
                    )
                if work_distance is not None and (
                    isinstance(work_distance, bool)
                    or not isinstance(work_distance, int)
                    or work_distance <= 0
                ):
                    raise TrainingSessionPrescriptionIntegrityError(
                        "La distance de travail doit être un entier strictement positif."
                    )
                if (work_duration is None) == (work_distance is None):
                    raise TrainingSessionPrescriptionIntegrityError(
                        "Une série doit définir exactement une durée ou une distance de travail."
                    )

                for target_key in (
                    "work_elevation_gain_meters",
                    "recovery_distance_meters",
                    "recovery_elevation_gain_meters",
                ):
                    target_value = interval.get(target_key)
                    if target_value is not None and (
                        isinstance(target_value, bool)
                        or not isinstance(target_value, int)
                        or target_value <= 0
                    ):
                        raise TrainingSessionPrescriptionIntegrityError(
                            f"La cible {target_key} doit être un entier strictement positif."
                        )

                recovery_duration = interval.get("recovery_duration")
                recovery_unit = interval.get("recovery_unit")
                if recovery_duration is None and recovery_unit is not None:
                    raise TrainingSessionPrescriptionIntegrityError(
                        "Une unité de récupération ne peut pas exister sans durée."
                    )
                if recovery_duration is not None and (
                    isinstance(recovery_duration, bool)
                    or not isinstance(recovery_duration, int)
                    or recovery_duration <= 0
                    or recovery_unit not in {"seconds", "minutes"}
                ):
                    raise TrainingSessionPrescriptionIntegrityError(
                        "La durée ou l'unité de récupération d'une série est invalide."
                    )
                if (
                    interval.get("recovery_distance_meters") is not None
                    and interval.get("recovery_elevation_gain_meters") is not None
                ):
                    raise TrainingSessionPrescriptionIntegrityError(
                        "Une récupération ne peut pas cibler simultanément une distance et un dénivelé."
                    )
                if (
                    (
                        interval.get("recovery_distance_meters") is not None
                        or interval.get("recovery_elevation_gain_meters") is not None
                    )
                    and recovery_duration is None
                ):
                    raise TrainingSessionPrescriptionIntegrityError(
                        "Une cible de récupération distance/D+ doit conserver une durée de planification."
                    )
        has_recovery = (
            isinstance(intervals, list)
            and any(
                isinstance(interval, dict)
                and any(
                    interval.get(key) is not None
                    for key in (
                        "recovery_duration",
                        "recovery_distance_meters",
                        "recovery_elevation_gain_meters",
                    )
                )
                for interval in intervals
            )
        )
        if has_recovery and prescription.get("recovery_intensity") is None:
            raise TrainingSessionPrescriptionIntegrityError(
                "Une séance fractionnée doit conserver une intensité dédiée aux récupérations."
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
    if version == 2:
        _validate_intensity_targets(
            intensity,
            context="globale de la séance",
        )
