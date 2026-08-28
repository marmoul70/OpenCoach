"""Génération déterministe des séances physiologiques."""

from __future__ import annotations

from opencoach.physiology.testing.models import (
    PhysiologicalTestType,
)
from opencoach.physiology.testing.session import (
    PhysiologicalTestSegmentIntensity,
    PhysiologicalTestSegmentType,
    PhysiologicalTestSession,
    PhysiologicalTestSessionSegment,
)


def generate_physiological_test_session(
    protocol: PhysiologicalTestType,
) -> PhysiologicalTestSession:
    """Génère une séance exécutable pour un protocole supporté."""

    if (
        protocol
        is PhysiologicalTestType.HALF_COOPER
    ):
        return _generate_half_cooper()

    if (
        protocol
        is PhysiologicalTestType.THRESHOLD_20_MIN
    ):
        return _generate_threshold_20_min()

    if (
        protocol
        is PhysiologicalTestType.UPHILL_6_MIN
    ):
        return _generate_uphill_6_min()

    raise NotImplementedError(
        "La génération de séance n'est pas encore "
        f"implémentée pour {protocol.value}."
    )


def _generate_half_cooper() -> PhysiologicalTestSession:
    return PhysiologicalTestSession(
        protocol=(
            PhysiologicalTestType.HALF_COOPER
        ),
        title="Test VMA — Demi-Cooper 6 min",
        description=(
            "Test terrain maximal de six minutes destiné "
            "à mettre à jour l'estimation de VMA."
        ),
        segments=(
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.WARMUP
                ),
                title="Échauffement",
                instruction=(
                    "Courir 20 minutes en endurance facile."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.EASY
                ),
                duration_seconds=20 * 60,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.PREPARATION
                ),
                title="Préparation",
                instruction=(
                    "Réaliser 4 accélérations progressives "
                    "de 20 secondes avec 60 secondes de "
                    "récupération facile."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.HARD
                ),
                repetitions=4,
                repetition_duration_seconds=20,
                recovery_duration_seconds=60,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.TEST
                ),
                title="Demi-Cooper",
                instruction=(
                    "Courir pendant exactement 6 minutes "
                    "au meilleur effort régulier possible. "
                    "L'objectif est de parcourir la plus "
                    "grande distance possible sans partir "
                    "trop vite."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.MAXIMAL
                ),
                duration_seconds=6 * 60,
                analysis_window=True,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.COOLDOWN
                ),
                title="Retour au calme",
                instruction=(
                    "Courir 10 à 15 minutes très facilement."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.EASY
                ),
                duration_seconds=12 * 60,
            ),
        ),
        terrain_requirements=(
            "Terrain plat.",
            "Surface régulière.",
            "Distance mesurable avec précision.",
            "Éviter une forte exposition au vent.",
        ),
        execution_notes=(
            "Effectuer le test en étant correctement récupéré.",
            "Éviter de réaliser le test par forte chaleur.",
            "Utiliser idéalement une ceinture cardio.",
            "Ne pas interrompre l'enregistrement pendant les 6 minutes.",
        ),
        expected_total_duration_minutes=44,
        metadata=(
            (
                "opencoach_session_kind",
                "physiological_test",
            ),
            (
                "test_protocol",
                PhysiologicalTestType.HALF_COOPER.value,
            ),
            (
                "analysis_window",
                "test_segment",
            ),
            (
                "expected_test_duration_seconds",
                "360",
            ),
        ),
    )


def _generate_threshold_20_min() -> PhysiologicalTestSession:
    return PhysiologicalTestSession(
        protocol=(
            PhysiologicalTestType.THRESHOLD_20_MIN
        ),
        title="Test seuil — 20 min",
        description=(
            "Effort continu de vingt minutes destiné "
            "à documenter l'allure et la fréquence "
            "cardiaque soutenables à haute intensité."
        ),
        segments=(
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.WARMUP
                ),
                title="Échauffement",
                instruction=(
                    "Courir 20 minutes progressivement, "
                    "principalement en endurance facile."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.EASY
                ),
                duration_seconds=20 * 60,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.PREPARATION
                ),
                title="Préparation",
                instruction=(
                    "Réaliser 3 accélérations progressives "
                    "de 30 secondes avec 90 secondes de "
                    "récupération."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.HARD
                ),
                repetitions=3,
                repetition_duration_seconds=30,
                recovery_duration_seconds=90,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.TEST
                ),
                title="Effort 20 min",
                instruction=(
                    "Courir 20 minutes au meilleur effort "
                    "régulier soutenable. L'allure doit être "
                    "contrôlée dès le départ et rester aussi "
                    "stable que possible."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.MAXIMAL
                ),
                duration_seconds=20 * 60,
                analysis_window=True,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.COOLDOWN
                ),
                title="Retour au calme",
                instruction=(
                    "Courir 10 à 15 minutes en endurance "
                    "très facile."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.EASY
                ),
                duration_seconds=12 * 60,
            ),
        ),
        terrain_requirements=(
            "Terrain plat ou très faiblement vallonné.",
            "Éviter les arrêts et croisements.",
            "Surface permettant une allure régulière.",
        ),
        execution_notes=(
            "Ne pas partir comme sur un effort de 5 minutes.",
            "Chercher une allure régulière sur l'ensemble des 20 minutes.",
            "Utiliser idéalement une ceinture cardio.",
            "Conserver l'enregistrement cardio complet.",
        ),
        expected_total_duration_minutes=58,
        metadata=(
            (
                "opencoach_session_kind",
                "physiological_test",
            ),
            (
                "test_protocol",
                PhysiologicalTestType.THRESHOLD_20_MIN.value,
            ),
            (
                "analysis_window",
                "test_segment",
            ),
            (
                "expected_test_duration_seconds",
                "1200",
            ),
        ),
    )


def _generate_uphill_6_min() -> PhysiologicalTestSession:
    return PhysiologicalTestSession(
        protocol=(
            PhysiologicalTestType.UPHILL_6_MIN
        ),
        title="Test trail — Montée 6 min",
        description=(
            "Test OpenCoach de suivi de la capacité "
            "ascensionnelle courte."
        ),
        segments=(
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.WARMUP
                ),
                title="Échauffement",
                instruction=(
                    "Courir 20 minutes facilement avec "
                    "quelques minutes sur terrain vallonné."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.EASY
                ),
                duration_seconds=20 * 60,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.PREPARATION
                ),
                title="Préparation spécifique",
                instruction=(
                    "Réaliser 3 accélérations de 30 secondes "
                    "en montée avec retour facile."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.HARD
                ),
                repetitions=3,
                repetition_duration_seconds=30,
                recovery_duration_seconds=90,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.TEST
                ),
                title="Montée 6 min",
                instruction=(
                    "Monter pendant exactement 6 minutes "
                    "au meilleur effort régulier possible. "
                    "Courir ou marcher uniquement si la pente "
                    "l'impose naturellement, sans interruption."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.MAXIMAL
                ),
                duration_seconds=6 * 60,
                analysis_window=True,
            ),
            PhysiologicalTestSessionSegment(
                segment_type=(
                    PhysiologicalTestSegmentType.COOLDOWN
                ),
                title="Retour au calme",
                instruction=(
                    "Récupérer puis courir 10 à 15 minutes "
                    "facilement."
                ),
                intensity=(
                    PhysiologicalTestSegmentIntensity.EASY
                ),
                duration_seconds=12 * 60,
            ),
        ),
        terrain_requirements=(
            "Montée continue pendant au moins 6 minutes.",
            "Pente aussi régulière que possible.",
            "Segment reproductible pour les futurs tests.",
            "Absence de descente pendant le segment test.",
        ),
        execution_notes=(
            "Utiliser si possible toujours la même montée.",
            "Éviter une montée très technique.",
            "Utiliser idéalement une ceinture cardio.",
            "Le D+ et la durée doivent être exploitables après synchronisation.",
        ),
        expected_total_duration_minutes=43,
        metadata=(
            (
                "opencoach_session_kind",
                "physiological_test",
            ),
            (
                "test_protocol",
                PhysiologicalTestType.UPHILL_6_MIN.value,
            ),
            (
                "analysis_window",
                "test_segment",
            ),
            (
                "expected_test_duration_seconds",
                "360",
            ),
        ),
    )
