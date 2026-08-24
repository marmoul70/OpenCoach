"""Mapping des séances générées vers le modèle persistant OpenCoach."""

from __future__ import annotations

from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.sessions.prescription import (
    IntensityReference,
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
        intensity=_build_intensity(
            generated
        ),
        heart_rate_zone=(
            _build_heart_rate_zone(
                generated
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


def _build_intensity(
    generated: GeneratedTrainingSession,
) -> str:
    """Construit le résumé d'intensité utilisé par l'ancien modèle."""

    prescription = (
        generated.proposal
        .intensity_prescription
    )

    if prescription is None:
        return ""

    return " / ".join(
        _format_target(
            target
        )
        for target in prescription.targets
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
