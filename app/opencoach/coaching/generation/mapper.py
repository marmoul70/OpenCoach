"""Mapping des séances générées vers le modèle persistant OpenCoach."""

from __future__ import annotations

from dataclasses import (
    fields,
    is_dataclass,
)
from enum import Enum

from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.sessions.prescription import (
    IntensityReference,
)
from opencoach.planning.sessions.prescription.physiological import (
    canonical_intensity_for_stimulus,
)
from opencoach.planning.stimulus.training import (
    TrainingModality,
)

from .models import (
    GeneratedTrainingSession,
)


def generated_session_to_training_session(
    generated: GeneratedTrainingSession,
    *,
    planning_key: str,
    existing_id=None,
) -> TrainingSession:
    """Convertit une séance générée vers le modèle persistant."""

    proposal = generated.proposal

    return TrainingSession(
        id=existing_id,
        date=generated.date,
        type=_resolve_session_type(
            generated
        ),
        sport_type=_resolve_sport_type(
            proposal.modality
        ),
        title=proposal.title,
        description=_build_description(
            generated
        ),
        duration_minutes=(
            proposal.duration_minutes
        ),
        distance_km=None,
        elevation_gain_m=None,
        planning_key=planning_key,
        intensity=(
            canonical_intensity_for_stimulus(
                proposal.covered_stimuli[0]
            )
        ),
        heart_rate_zone=(
            _build_heart_rate_zone(
                generated
            )
        ),
        prescription=(
            _serialize_prescription(
                proposal,
                vma_kmh=generated.vma_kmh,
            )
        ),
        status="planned",
        activity_id=None,
    )


def _resolve_session_type(
    generated: GeneratedTrainingSession,
) -> str:
    """Utilise le stimulus principal comme type métier."""

    return (
        generated.proposal
        .covered_stimuli[0]
        .value
    )


def _resolve_sport_type(
    modality: TrainingModality,
) -> str:
    """Convertit la modalité métier vers le champ historique sport_type."""

    mapping = {
        TrainingModality.RUNNING: "Run",
        TrainingModality.TRAIL_RUNNING: "TrailRun",
        TrainingModality.CYCLING: "Ride",
        TrainingModality.STRENGTH: "Strength",
    }

    return mapping.get(
        modality,
        modality.value,
    )


def _build_description(
    generated: GeneratedTrainingSession,
) -> str:
    """Produit une description lisible à partir des objets structurés."""

    proposal = generated.proposal

    sections = [
        proposal.objective,
    ]

    for block in proposal.blocks:
        duration = (
            f"{block.duration_minutes} min"
            if block.duration_minutes is not None
            else "durée libre"
        )

        sections.append(
            (
                f"{block.name} — "
                f"{duration} : "
                f"{block.description}"
            )
        )

    prescription = (
        proposal.intensity_prescription
    )

    if prescription is not None:
        targets = ", ".join(
            _format_target(
                target
            )
            for target in prescription.targets
        )

        sections.append(
            f"Intensité : {targets}"
        )

        sections.extend(
            prescription.guidance
        )

    if proposal.coach_notes:
        sections.extend(
            proposal.coach_notes
        )

    return "\n".join(
        section
        for section in sections
        if section.strip()
    )



def _serialize_prescription(
    proposal,
    *,
    vma_kmh: float | None = None,
) -> dict:
    """Sérialise la prescription structurée d'une séance.

    Le format est explicitement versionné afin de pouvoir faire
    évoluer la prescription persistée sans dépendre directement
    de l'implémentation Python des dataclasses métier.
    """

    return {
        "version": 1,
        "blocks": [
            {
                "name": block.name,
                "description": (
                    block.description
                ),
                "duration_minutes": (
                    block.duration_minutes
                ),
            }
            for block in proposal.blocks
        ],
        "work_structure": (
            _serialize_work_structure(
                proposal.work_structure
            )
            if proposal.work_structure
            is not None
            else None
        ),
        "intensity": (
            _serialize_intensity_prescription(
                proposal.intensity_prescription,
                vma_kmh=vma_kmh,
            )
            if proposal.intensity_prescription
            is not None
            else None
        ),
    }


def _serialize_work_structure(
    structure,
) -> dict:
    """Sérialise la structure concrète du bloc principal."""

    return {
        "type": (
            structure.structure_type.value
        ),
        "stimulus": (
            structure.stimulus.value
        ),
        "available_minutes": (
            structure.available_minutes
        ),
        "continuous_minutes": (
            structure.continuous_minutes
        ),
        "description": (
            structure.description
        ),
        "circuit": (
            _to_json_value(
                structure.circuit
            )
            if structure.circuit
            is not None
            else None
        ),
        "intervals": [
            _serialize_work_interval(
                interval
            )
            for interval
            in structure.intervals
        ],
    }


def _serialize_work_interval(
    interval,
) -> dict:
    """Sérialise une série de répétitions."""

    return {
        "repetitions": (
            interval.repetitions
        ),
        "work_duration": (
            interval.work_duration
        ),
        "work_unit": (
            interval.work_unit.value
            if interval.work_unit
            is not None
            else None
        ),
        "work_distance_meters": (
            interval.work_distance_meters
        ),
        "repetition_target": (
            _to_json_value(
                interval.repetition_target
            )
            if interval.repetition_target
            is not None
            else None
        ),
        "recovery_duration": (
            interval.recovery_duration
        ),
        "recovery_unit": (
            interval.recovery_unit.value
            if interval.recovery_unit
            is not None
            else None
        ),
    }


def _serialize_intensity_target(
    target,
    *,
    vma_kmh: float | None = None,
) -> dict:
    """Sérialise une cible et ses dérivés individualisés."""

    payload = _to_json_value(
        target
    )

    if (
        target.reference
        is not IntensityReference.VMA_PERCENT
        or vma_kmh is None
        or vma_kmh <= 0
    ):
        return payload

    minimum_speed = (
        vma_kmh
        * target.minimum
        / 100
    )

    maximum_speed = (
        vma_kmh
        * target.maximum
        / 100
    )

    if (
        minimum_speed <= 0
        or maximum_speed <= 0
    ):
        return payload

    payload["derived"] = {
        "vma_kmh": (
            round(
                vma_kmh,
                3,
            )
        ),
        "speed_kmh": {
            "minimum": round(
                minimum_speed,
                3,
            ),
            "maximum": round(
                maximum_speed,
                3,
            ),
        },
        "pace_seconds_per_km": {
            # Une vitesse élevée produit
            # l'allure la plus rapide.
            "fastest": round(
                3600
                / maximum_speed,
                2,
            ),
            "slowest": round(
                3600
                / minimum_speed,
                2,
            ),
        },
    }

    return payload


def _serialize_intensity_prescription(
    prescription,
    *,
    vma_kmh: float | None = None,
) -> dict:
    """Sérialise toutes les cibles physiologiques calculées.

    Les valeurs numériques restent brutes afin de permettre
    ultérieurement :
    - l'affichage des zones et allures ;
    - la comparaison prévu / réalisé ;
    - l'analyse physiologique des activités synchronisées.
    """

    return {
        "targets": [
            _serialize_intensity_target(
                target,
                vma_kmh=vma_kmh,
            )
            for target
            in prescription.targets
        ],
        "guidance": list(
            prescription.guidance
        ),
    }


def _to_json_value(
    value,
):
    """Convertit récursivement les objets métier en JSON natif.

    Ce helper permet notamment de conserver les objets
    DistanceRepetitionTarget et WorkCircuit sans transformer
    leurs données numériques en texte.
    """

    if value is None:
        return None

    if isinstance(
        value,
        Enum,
    ):
        return value.value

    if is_dataclass(
        value
    ):
        return {
            field.name: (
                _to_json_value(
                    getattr(
                        value,
                        field.name,
                    )
                )
            )
            for field
            in fields(
                value
            )
        }

    if isinstance(
        value,
        tuple
        | list,
    ):
        return [
            _to_json_value(
                item
            )
            for item
            in value
        ]

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): (
                _to_json_value(
                    item
                )
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    raise TypeError(
        "Valeur de prescription "
        f"non sérialisable : {type(value)!r}"
    )


def _build_heart_rate_zone(
    generated: GeneratedTrainingSession,
) -> str | None:
    """Extrait une cible cardiaque lisible si elle existe."""

    prescription = (
        generated.proposal
        .intensity_prescription
    )

    if prescription is None:
        return None

    for reference in (
        IntensityReference.HEART_RATE,
        IntensityReference.HEART_RATE_RESERVE,
    ):
        target = prescription.target_for(
            reference
        )

        if target is not None:
            return _format_target(
                target
            )

    return None


def _format_target(
    target,
) -> str:
    """Formate une cible d'intensité sans perdre son unité."""

    minimum = _format_number(
        target.minimum
    )

    maximum = _format_number(
        target.maximum
    )

    return (
        f"{target.label}: "
        f"{minimum}–{maximum} "
        f"{target.unit}"
    )


def _format_number(
    value: float,
) -> str:
    if float(
        value
    ).is_integer():
        return str(
            int(
                value
            )
        )

    return (
        f"{value:.1f}"
        .rstrip("0")
        .rstrip(".")
    )
