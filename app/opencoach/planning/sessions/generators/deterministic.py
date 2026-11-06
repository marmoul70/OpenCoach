"""Générateur déterministe de séances OpenCoach."""

from __future__ import annotations
from math import ceil

from dataclasses import dataclass, replace

from opencoach.planning.sessions.coach_port import (
    SessionCoachRequest,
)
from opencoach.planning.sessions.generators.catalog import (
    SessionRecipe,
    SessionStructure,
    get_session_recipe,
    validate_session_recipe_catalog,
)
from opencoach.planning.sessions.intent import (
    SessionIntentImportance,
)
from opencoach.planning.sessions.prescription.distance_target import (
    calculate_distance_repetition_target,
)
from opencoach.planning.sessions.prescription.intervals import (
    WorkStructure,
    build_work_structure,
)
from opencoach.planning.sessions.prescription.models import (
    IntensityReference,
    SessionIntensityPrescription,
)
from opencoach.planning.sessions.prescription.physiological import (
    build_intensity_prescription,
)
from opencoach.planning.sessions.proposal import (
    SessionBlock,
    SessionProposal,
)
from opencoach.planning.stimulus.training import (
    TrainingModality,
    TrainingStimulus,
)


_DEFAULT_DURATION_BY_IMPORTANCE = {
    SessionIntentImportance.SUPPORT: 45,
    SessionIntentImportance.IMPORTANT: 60,
    SessionIntentImportance.KEY: 90,
}


@dataclass(frozen=True, slots=True)
class DeterministicSessionGenerator:
    """Transforme une intention planifiée en séance concrète.

    Le générateur ne modifie jamais :

    - le jour retenu ;
    - les stimuli demandés ;
    - les contraintes de durée ;
    - les modalités imposées.

    Il matérialise uniquement une intention déjà décidée par
    le moteur de planification OpenCoach.
    """

    def __post_init__(
        self,
    ) -> None:
        validate_session_recipe_catalog()

    def generate_session(
        self,
        *,
        request: SessionCoachRequest,
    ) -> SessionProposal:
        """Génère une séance déterministe."""

        intent = request.slot.intent

        recipe = get_session_recipe(
            intent.primary_stimulus
        )

        duration = _resolve_duration(
            request
        )

        modality = _resolve_modality(
            request=request,
            recipe=recipe,
        )

        blocks, work_structure = (
            _build_session_content(
                request=request,
                duration_minutes=duration,
                recipe=recipe,
            )
        )

        intensity_prescription = (
            build_intensity_prescription(
                stimulus=(
                    intent.primary_stimulus
                ),
                physiology=(
                    request.physiology
                ),
            )
        )

        work_structure = (
            _enrich_distance_repetition_targets(
                work_structure=work_structure,
                intensity_prescription=(
                    intensity_prescription
                ),
                request=request,
            )
        )

        # Chaque phase reçoit sa propre prescription. Les phases de mise en
        # route et de récupération utilisent une cible facile, sans hériter
        # artificiellement de l'intensité du travail principal.
        easy_intensity = build_intensity_prescription(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            physiology=request.physiology,
        )
        blocks = tuple(
            replace(
                block,
                intensity_prescription=(
                    intensity_prescription
                    if block.phase == "main"
                    else easy_intensity
                ),
            )
            if block.phase in {"main", "warmup", "easy", "cooldown"}
            else block
            for block in blocks
        )

        return SessionProposal(
            title=recipe.title,
            modality=modality,
            duration_minutes=duration,
            covered_stimuli=(
                intent.stimuli
            ),
            blocks=blocks,
            objective=recipe.objective,
            intensity_prescription=(
                intensity_prescription
            ),
            recovery_intensity_prescription=easy_intensity,
            work_structure=(
                work_structure
            ),
            coach_notes=_build_coach_notes(
                request
            ),
        )


def _enrich_distance_repetition_targets(
    *,
    work_structure: WorkStructure,
    intensity_prescription: SessionIntensityPrescription,
    request: SessionCoachRequest,
) -> WorkStructure:
    """Individualise les répétitions métriques à partir de la VMA.

    Aucun chrono n'est produit lorsque la VMA n'est pas utilisable
    ou lorsque la séance ne possède pas de cible en pourcentage de VMA.
    """

    if not work_structure.intervals:
        return work_structure

    physiology = request.physiology

    if physiology is None:
        return work_structure

    vma_metric = physiology.vma

    if (
        not vma_metric.usable
        or vma_metric.value is None
        or vma_metric.value <= 0
    ):
        return work_structure

    vma_target = (
        intensity_prescription.target_for(
            IntensityReference.VMA_PERCENT
        )
    )

    if vma_target is None:
        return work_structure

    enriched_intervals = []

    changed = False

    for interval in work_structure.intervals:
        distance_meters = (
            interval.work_distance_meters
        )

        if distance_meters is None:
            enriched_intervals.append(
                interval
            )
            continue

        repetition_target = (
            calculate_distance_repetition_target(
                distance_meters=distance_meters,
                vma_kmh=vma_metric.value,
                vma_percent_min=(
                    vma_target.minimum
                ),
                vma_percent_max=(
                    vma_target.maximum
                ),
            )
        )

        enriched_intervals.append(
            replace(
                interval,
                repetition_target=(
                    repetition_target
                ),
            )
        )

        changed = True

    if not changed:
        return work_structure

    return replace(
        work_structure,
        intervals=tuple(
            enriched_intervals
        ),
    )


def _resolve_duration(
    request: SessionCoachRequest,
) -> int:
    """Choisit une durée déterministe compatible avec le créneau."""

    intent = request.slot.intent

    if request.planned_duration_minutes is not None:
        duration = request.planned_duration_minutes

        minimum = intent.duration_min_minutes
        maximum = intent.duration_max_minutes
        available = (
            request.slot.duration_available_minutes
        )

        if (
            minimum is not None
            and duration < minimum
        ):
            raise ValueError(
                "La durée planifiée est inférieure "
                "à la durée minimale de l'intention."
            )

        if (
            maximum is not None
            and duration > maximum
        ):
            raise ValueError(
                "La durée planifiée dépasse "
                "la durée maximale de l'intention."
            )

        if (
            available is not None
            and duration > available
        ):
            raise ValueError(
                "La durée planifiée dépasse "
                "la disponibilité du créneau."
            )

        return duration

    minimum = (
        intent.duration_min_minutes
    )

    maximum = (
        intent.duration_max_minutes
    )

    available = (
        request.slot.duration_available_minutes
    )

    if (
        minimum is not None
        and maximum is not None
    ):
        duration = _round_to_five(
            (
                minimum
                + maximum
            )
            / 2
        )

    elif minimum is not None:
        duration = minimum

    elif maximum is not None:
        default_duration = (
            _DEFAULT_DURATION_BY_IMPORTANCE[
                intent.importance
            ]
        )

        duration = min(
            default_duration,
            maximum,
        )

    else:
        duration = (
            _DEFAULT_DURATION_BY_IMPORTANCE[
                intent.importance
            ]
        )

    if available is not None:
        duration = min(
            duration,
            available,
        )

    if (
        minimum is not None
        and duration < minimum
    ):
        raise ValueError(
            "La durée disponible est incompatible "
            "avec la durée minimale de l'intention."
        )

    if (
        maximum is not None
        and duration > maximum
    ):
        raise ValueError(
            "La durée calculée dépasse la durée "
            "maximale de l'intention."
        )

    return duration


def _resolve_modality(
    *,
    request: SessionCoachRequest,
    recipe: SessionRecipe,
) -> TrainingModality:
    """Choisit la modalité sans violer l'intention."""

    intent = request.slot.intent

    if intent.required_modalities:
        return intent.required_modalities[
            0
        ]

    if intent.preferred_modalities:
        return intent.preferred_modalities[
            0
        ]

    return recipe.default_modality


def _build_session_content(
    *,
    request: SessionCoachRequest,
    duration_minutes: int,
    recipe: SessionRecipe,
) -> tuple[
    tuple[
        SessionBlock,
        ...,
    ],
    WorkStructure,
]:
    """Construit les blocs et la structure du travail principal."""

    stimulus = (
        request.slot.intent.primary_stimulus
    )

    if (
        recipe.structure
        is SessionStructure.RECOVERY
    ):
        work_structure = (
            build_work_structure(
                stimulus=stimulus,
                phase=request.phase,
                phase_week_index=(
                    request.phase_week_index
                ),
                available_minutes=(
                    duration_minutes
                ),
            )
        )

        return (
            (
                SessionBlock(
                    name=(
                        recipe.main_block_name
                    ),
                    description=(
                        _merge_descriptions(
                            recipe.main_block_description,
                            work_structure.description,
                        )
                    ),
                    duration_minutes=(
                        duration_minutes
                    ),
                    phase="main",
                ),
            ),
            work_structure,
        )

    warmup, main_available, cooldown = (
        _split_duration(
            duration_minutes
        )
    )

    work_structure = (
        build_work_structure(
            stimulus=stimulus,
            phase=request.phase,
            phase_week_index=(
                request.phase_week_index
            ),
            available_minutes=(
                main_available
            ),
        )
    )

    blocks: list[
        SessionBlock
    ] = []

    if warmup > 0:
        blocks.append(
            SessionBlock(
                name="Échauffement",
                description=(
                    recipe.warmup_description
                ),
                duration_minutes=warmup,
                phase="warmup",
            )
        )

    blocks.append(
        SessionBlock(
            name=recipe.main_block_name,
            description=(
                _merge_descriptions(
                    recipe.main_block_description,
                    work_structure.description,
                )
            ),
            duration_minutes=ceil(
                work_structure.planned_minutes
            ),
            phase="main",
        )
    )

    planned_main_minutes = ceil(
        work_structure.planned_minutes
    )

    remaining_main_minutes = (
        main_available
        - planned_main_minutes
)

    if remaining_main_minutes > 0:
        blocks.append(
            SessionBlock(
                name="Complément facile",
                description=(
                    "Course facile ou récupération active "
                    "pour compléter le temps disponible "
                    "sans ajouter d'intensité."
                ),
                duration_minutes=(
                    remaining_main_minutes
                ),
                phase="easy",
            )
        )

    if cooldown > 0:
        blocks.append(
            SessionBlock(
                name="Retour au calme",
                description=(
                    recipe.cooldown_description
                ),
                duration_minutes=cooldown,
                phase="cooldown",
            )
        )

    return (
        tuple(
            blocks
        ),
        work_structure,
    )


def _split_duration(
    duration_minutes: int,
) -> tuple[
    int,
    int,
    int,
]:
    """Découpe une durée en échauffement, corps et retour au calme."""

    if duration_minutes < 30:
        return (
            0,
            duration_minutes,
            0,
        )

    if duration_minutes < 60:
        warmup = 10
        cooldown = 5

    elif duration_minutes < 120:
        warmup = 15
        cooldown = 10

    else:
        warmup = 20
        cooldown = 15

    main = (
        duration_minutes
        - warmup
        - cooldown
    )

    if main <= 0:
        raise ValueError(
            "La durée de séance est insuffisante "
            "pour construire les blocs."
        )

    return (
        warmup,
        main,
        cooldown,
    )


def _merge_descriptions(
    general: str,
    specific: str,
) -> str:
    """Combine la recette générique et la structure concrète."""

    return (
        f"{general} "
        f"Structure : {specific}"
    )


def _build_coach_notes(
    request: SessionCoachRequest,
) -> tuple[
    str,
    ...,
]:
    """Construit les notes explicatives de génération."""

    notes = [
        (
            "Séance générée de manière déterministe "
            "par le moteur Python OpenCoach."
        ),
        (
            "Phase d'entraînement : "
            f"{request.phase.value}."
        ),
    ]

    if (
        request.physiology is None
    ):
        notes.append(
            (
                "Prescription physiologique limitée : "
                "les données de calibration ne sont "
                "pas disponibles."
            )
        )

    if request.slot.notes:
        notes.append(
            request.slot.notes
        )

    notes.extend(
        _build_secondary_stimulus_guidance(request)
    )

    return tuple(
        notes
    )


def _round_to_five(
    value: float,
) -> int:
    """Arrondit une durée au multiple de cinq le plus proche."""

    return max(
        5,
        int(
            5
            * round(
                value / 5
            )
        ),
    )


def _build_secondary_stimulus_guidance(
    request: SessionCoachRequest,
) -> tuple[str, ...]:
    """Rend explicites les stimuli secondaires regroupés dans l'intention.

    Ces consignes restent qualitatives lorsque le parcours ou le matériel
    ne fournit pas de cible chiffrée fiable.
    """
    guidance_by_stimulus = {
        TrainingStimulus.UPHILL_STRENGTH: (
            "Stimulus complémentaire — montée : sur les côtes naturelles "
            "du parcours, privilégier une foulée dynamique, des appuis "
            "efficaces et une intensité maîtrisée."
        ),
        TrainingStimulus.UPHILL_STRENGTH_ENDURANCE: (
            "Stimulus complémentaire — force-endurance en côte : intégrer "
            "les montées disponibles en conservant une posture stable et "
            "une poussée régulière, sans ajouter de cible de D+ non prescrite."
        ),
        TrainingStimulus.DOWNHILL_SPECIFICITY: (
            "Stimulus complémentaire — descente : travailler le contrôle "
            "des appuis, la cadence et le relâchement sur des portions "
            "adaptées et sûres."
        ),
        TrainingStimulus.RACE_SPECIFIC: (
            "Stimulus complémentaire — spécificité course : choisir un "
            "terrain cohérent avec les contraintes connues de l'objectif. "
            "Aucune distance ni cible de D+ supplémentaire n'est supposée."
        ),
        TrainingStimulus.STRENGTH_CORE: (
            "Stimulus complémentaire — tronc : intégrer le travail de "
            "gainage et de stabilité prévu dans la séance, sans dépasser "
            "le temps alloué."
        ),
        TrainingStimulus.STRENGTH_LOWER_BODY: (
            "Stimulus complémentaire — membres inférieurs : intégrer le "
            "travail de force prévu dans la séance en conservant une "
            "exécution contrôlée."
        ),
    }

    return tuple(
        guidance_by_stimulus[stimulus]
        for stimulus in request.slot.intent.secondary_stimuli
        if stimulus in guidance_by_stimulus
    )
