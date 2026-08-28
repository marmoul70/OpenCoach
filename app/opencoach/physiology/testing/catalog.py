"""Catalogue des protocoles physiologiques OpenCoach."""

from __future__ import annotations

from opencoach.physiology.testing.models import (
    ActivityMetric,
    EvidenceLevel,
    PhysiologicalMetric,
    PhysiologicalTestProtocol,
    PhysiologicalTestType,
    SportDiscipline,
    PhysiologicalTestAcquisitionMode,
    PhysiologicalTestEffortLevel,
    PhysiologicalTestFatigueCost,
)


RUNNING = (
    SportDiscipline.ROAD_RUNNING,
    SportDiscipline.TRAIL_RUNNING,
    SportDiscipline.TRACK_RUNNING,
)


PHYSIOLOGICAL_TEST_CATALOG: tuple[
    PhysiologicalTestProtocol,
    ...,
] = (
    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.HALF_COOPER,
        name="Demi-Cooper 6 min",
        description=(
            "Effort maximal de six minutes utilisé "
            "pour estimer la vitesse aérobie de terrain."
        ),
        disciplines=RUNNING,
        target_metrics=(
            PhysiologicalMetric.VMA,
            PhysiologicalMetric.MAX_HEART_RATE,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.MAXIMAL,
        fatigue_cost=PhysiologicalTestFatigueCost.HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=48,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.DISTANCE,
            ActivityMetric.HEART_RATE,
        ),
        evidence_level=EvidenceLevel.FIELD_STANDARD,
        instructions=(
            "Réaliser le test sur terrain plat "
            "et mesuré.",
            "Effectuer un échauffement complet.",
            "Parcourir la plus grande distance "
            "possible en six minutes.",
            "Maintenir un effort aussi régulier "
            "que possible.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.COOPER_12_MIN,
        name="Cooper 12 min",
        description=(
            "Effort maximal de douze minutes utilisé "
            "comme test de performance aérobie."
        ),
        disciplines=RUNNING,
        target_metrics=(
            PhysiologicalMetric.VMA,
            PhysiologicalMetric.MAX_HEART_RATE,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.MAXIMAL,
        fatigue_cost=PhysiologicalTestFatigueCost.HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=48,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.DISTANCE,
            ActivityMetric.HEART_RATE,
        ),
        evidence_level=EvidenceLevel.FIELD_STANDARD,
        instructions=(
            "Utiliser un terrain plat et mesuré.",
            "Effectuer un échauffement complet.",
            "Parcourir la plus grande distance "
            "possible en douze minutes.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.VAMEVAL,
        name="VAMEVAL",
        description=(
            "Test progressif par paliers destiné "
            "à évaluer la vitesse aérobie maximale."
        ),
        disciplines=RUNNING,
        target_metrics=(
            PhysiologicalMetric.VMA,
            PhysiologicalMetric.MAX_HEART_RATE,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.MAXIMAL,
        fatigue_cost=PhysiologicalTestFatigueCost.HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=48,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.SPEED,
            ActivityMetric.HEART_RATE,
        ),
        evidence_level=(
            EvidenceLevel.RESEARCH_PROTOCOL
        ),
        instructions=(
            "Utiliser le protocole VAMEVAL "
            "standardisé.",
            "Respecter les paliers imposés.",
            "Poursuivre jusqu'à incapacité à "
            "maintenir la vitesse demandée.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.THRESHOLD_20_MIN,
        name="Test seuil 20 min",
        description=(
            "Contre-la-montre de vingt minutes "
            "utilisé pour documenter l'effort "
            "soutenu proche du seuil."
        ),
        disciplines=RUNNING,
        target_metrics=(
            PhysiologicalMetric.THRESHOLD_PACE,
            PhysiologicalMetric.THRESHOLD_HEART_RATE,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.PASSIVE,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.MAXIMAL,
        fatigue_cost=PhysiologicalTestFatigueCost.HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=48,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.DISTANCE,
            ActivityMetric.PACE,
            ActivityMetric.HEART_RATE_STREAM,
        ),
        evidence_level=(
            EvidenceLevel.OPENCOACH_MONITORING
        ),
        instructions=(
            "Effectuer un échauffement complet.",
            "Réaliser vingt minutes au meilleur "
            "effort régulier soutenable.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.THRESHOLD_30_MIN,
        name="Test seuil 30 min",
        description=(
            "Contre-la-montre de trente minutes "
            "pour l'estimation terrain de paramètres "
            "associés au seuil."
        ),
        disciplines=RUNNING,
        target_metrics=(
            PhysiologicalMetric.THRESHOLD_PACE,
            PhysiologicalMetric.THRESHOLD_HEART_RATE,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.PASSIVE,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.MAXIMAL,
        fatigue_cost=PhysiologicalTestFatigueCost.VERY_HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=72,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.DISTANCE,
            ActivityMetric.PACE,
            ActivityMetric.HEART_RATE_STREAM,
        ),
        evidence_level=(
            EvidenceLevel.RESEARCH_PROTOCOL
        ),
        instructions=(
            "Effectuer un échauffement complet.",
            "Réaliser trente minutes au meilleur "
            "effort régulier soutenable.",
            "Conserver les données cardio détaillées "
            "pour l'analyse de la fenêtre utile.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=(
            PhysiologicalTestType
            .CRITICAL_SPEED_MULTI_EFFORT
        ),
        name="Critical Speed multi-efforts",
        description=(
            "Estimation de la Critical Speed à partir "
            "de plusieurs performances maximales "
            "de durées différentes."
        ),
        disciplines=RUNNING,
        target_metrics=(
            PhysiologicalMetric.CRITICAL_SPEED,
            PhysiologicalMetric.D_PRIME,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.PASSIVE,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.MAXIMAL,
        fatigue_cost=PhysiologicalTestFatigueCost.HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=48,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.DISTANCE,
            ActivityMetric.PACE,
        ),
        evidence_level=(
            EvidenceLevel.RESEARCH_PROTOCOL
        ),
        instructions=(
            "Utiliser plusieurs performances "
            "maximales de durées différentes.",
            "Privilégier les performances récentes "
            "et réalisées dans des conditions "
            "comparables.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.UPHILL_6_MIN,
        name="Montée 6 min",
        description=(
            "Test OpenCoach de suivi de la capacité "
            "ascensionnelle courte."
        ),
        disciplines=(
            SportDiscipline.TRAIL_RUNNING,
        ),
        target_metrics=(
            PhysiologicalMetric.UPHILL_VAM,
            PhysiologicalMetric.MAX_HEART_RATE,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.PASSIVE,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.MAXIMAL,
        fatigue_cost=PhysiologicalTestFatigueCost.HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=48,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.DISTANCE,
            ActivityMetric.ELEVATION_GAIN,
            ActivityMetric.HEART_RATE,
        ),
        evidence_level=(
            EvidenceLevel.OPENCOACH_MONITORING
        ),
        instructions=(
            "Utiliser une montée régulière et "
            "reproductible.",
            "Réaliser six minutes au meilleur effort "
            "régulier possible.",
            "Réutiliser si possible le même segment "
            "lors des évaluations suivantes.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.UPHILL_20_MIN,
        name="Montée 20 min",
        description=(
            "Test OpenCoach de capacité ascensionnelle "
            "soutenue."
        ),
        disciplines=(
            SportDiscipline.TRAIL_RUNNING,
        ),
        target_metrics=(
            PhysiologicalMetric.UPHILL_SUSTAINED_VAM,
            PhysiologicalMetric.THRESHOLD_HEART_RATE,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.PASSIVE,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.HARD,
        fatigue_cost=PhysiologicalTestFatigueCost.HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=48,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.DISTANCE,
            ActivityMetric.ELEVATION_GAIN,
            ActivityMetric.HEART_RATE_STREAM,
        ),
        evidence_level=(
            EvidenceLevel.OPENCOACH_MONITORING
        ),
        instructions=(
            "Utiliser une montée régulière et "
            "suffisamment longue.",
            "Maintenir un effort soutenu et régulier "
            "pendant vingt minutes.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.INCREMENTRAIL,
        name="IncremenTrail",
        description=(
            "Test incrémental spécifique à la course "
            "en montée raide."
        ),
        disciplines=(
            SportDiscipline.TRAIL_RUNNING,
        ),
        target_metrics=(
            PhysiologicalMetric.UPHILL_VAM,
            PhysiologicalMetric.MAX_HEART_RATE,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.MANUAL,
        ),
        effort_level=PhysiologicalTestEffortLevel.MAXIMAL,
        fatigue_cost=PhysiologicalTestFatigueCost.VERY_HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=72,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.SPEED,
            ActivityMetric.ELEVATION_GAIN,
            ActivityMetric.HEART_RATE,
        ),
        evidence_level=(
            EvidenceLevel.RESEARCH_PROTOCOL
        ),
        instructions=(
            "Respecter le protocole IncremenTrail "
            "standardisé.",
            "Ce protocole est réservé aux situations "
            "où son environnement peut être "
            "correctement reproduit.",
        ),
    ),

    PhysiologicalTestProtocol(
        id=PhysiologicalTestType.TRAIL_DURABILITY,
        name="Durabilité trail",
        description=(
            "Évaluation OpenCoach de la dégradation "
            "d'une performance standardisée après "
            "un effort prolongé."
        ),
        disciplines=(
            SportDiscipline.TRAIL_RUNNING,
        ),
        target_metrics=(
            PhysiologicalMetric.TRAIL_DURABILITY,
        ),
        acquisition_modes=(
            PhysiologicalTestAcquisitionMode.SCHEDULED,
            PhysiologicalTestAcquisitionMode.PASSIVE,
        ),
        effort_level=PhysiologicalTestEffortLevel.HARD,
        fatigue_cost=PhysiologicalTestFatigueCost.VERY_HIGH,
        replaces_quality_session=True,
        minimum_recovery_before_hours=48,
        minimum_recovery_after_hours=72,
        required_activity_metrics=(
            ActivityMetric.DURATION,
            ActivityMetric.DISTANCE,
            ActivityMetric.ELEVATION_GAIN,
            ActivityMetric.HEART_RATE_STREAM,
            ActivityMetric.INTERVALS,
        ),
        evidence_level=(
            EvidenceLevel.OPENCOACH_MONITORING
        ),
        instructions=(
            "Comparer une performance standardisée "
            "avant et après une charge prolongée.",
            "Utiliser un parcours ou segment aussi "
            "reproductible que possible.",
        ),
    ),
)


def get_test_protocol(
    test_type: PhysiologicalTestType,
) -> PhysiologicalTestProtocol:
    """Retourne un protocole par identifiant."""

    for protocol in PHYSIOLOGICAL_TEST_CATALOG:
        if protocol.id is test_type:
            return protocol

    raise KeyError(
        f"Protocole inconnu : {test_type}"
    )


def list_test_protocols_for_disciplines(
    disciplines: tuple[
        SportDiscipline,
        ...,
    ],
) -> tuple[
    PhysiologicalTestProtocol,
    ...,
]:
    """Retourne les tests compatibles avec les disciplines."""

    selected = set(
        disciplines
    )

    return tuple(
        protocol
        for protocol
        in PHYSIOLOGICAL_TEST_CATALOG
        if selected.intersection(
            protocol.disciplines
        )
    )


def list_test_protocols_for_metric(
    metric: PhysiologicalMetric,
) -> tuple[
    PhysiologicalTestProtocol,
    ...,
]:
    """Retourne les protocoles capables d'estimer une métrique."""

    return tuple(
        protocol
        for protocol
        in PHYSIOLOGICAL_TEST_CATALOG
        if metric
        in protocol.target_metrics
    )
