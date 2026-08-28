"""Guidage détaillé universel des séances OpenCoach.

Ce module transforme une TrainingSession persistée en fiche explicative
destinée à l'athlète.

La fiche constitue également le futur contrat entre :
- le moteur qui prescrit la séance ;
- l'interface qui explique la séance ;
- l'analyseur qui comparera le prévu au réalisé.

Le modèle TrainingSession reste volontairement léger.
Les explications riches sont dérivées dans cette couche dédiée.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.models import (
    TrainingSession,
)


@dataclass(
    frozen=True,
    slots=True,
)
class SessionGuidanceIntensityTarget:
    """Cible physiologique affichable dans la fiche athlète."""

    reference: str
    label: str

    minimum: float
    maximum: float

    unit: str

    speed_min_kmh: float | None = None
    speed_max_kmh: float | None = None

    pace_fastest_seconds_per_km: float | None = None
    pace_slowest_seconds_per_km: float | None = None


@dataclass(
    frozen=True,
    slots=True,
)
class SessionGuidanceStep:
    """Bloc exécutable d'une séance."""

    title: str
    description: str

    duration_minutes: int | None = None

    intensity_target: str | None = None
    heart_rate_target: str | None = None

    intensity_targets: tuple[
        SessionGuidanceIntensityTarget,
        ...,
    ] = ()

    repetitions: int | None = None

    work_distance_meters: int | None = None

    repetition_fast_seconds: float | None = None
    repetition_slow_seconds: float | None = None

    recovery_description: str | None = None


@dataclass(
    frozen=True,
    slots=True,
)
class SessionGuidance:
    """Fiche détaillée universelle d'une séance."""

    session_type: str

    objective: str

    coach_rationale: str

    terrain_recommendation: str

    preparation: tuple[
        str,
        ...,
    ]

    warmup: tuple[
        SessionGuidanceStep,
        ...,
    ]

    main_set: tuple[
        SessionGuidanceStep,
        ...,
    ]

    cooldown: tuple[
        SessionGuidanceStep,
        ...,
    ]

    execution_advice: tuple[
        str,
        ...,
    ]

    warnings: tuple[
        str,
        ...,
    ]

    analysis_targets: tuple[
        str,
        ...,
    ]


def build_session_guidance(
    session: TrainingSession,
) -> SessionGuidance:
    """Construit la fiche correspondant à une séance réelle."""

    builders = {
        "aerobic_easy": (
            _build_aerobic_easy
        ),
        "long_endurance": (
            _build_long_endurance
        ),
        "threshold": (
            _build_threshold
        ),
        "vo2max": (
            _build_vo2max
        ),
        "speed_development": (
            _build_speed_development
        ),
        "strength_lower_body": (
            _build_strength_lower_body
        ),
        "rest": (
            _build_rest
        ),
        "supplementary": (
            _build_supplementary
        ),
    }

    builder = builders.get(
        session.type,
        _build_generic,
    )

    return builder(
        session
    )


def _build_intensity_targets(
    session: TrainingSession,
) -> tuple[
    SessionGuidanceIntensityTarget,
    ...,
]:
    """Construit les cibles affichables depuis la prescription persistée."""

    prescription = (
        session.prescription
    )

    if not isinstance(
        prescription,
        dict,
    ):
        return ()

    intensity = prescription.get(
        "intensity"
    )

    if not isinstance(
        intensity,
        dict,
    ):
        return ()

    raw_targets = intensity.get(
        "targets"
    )

    if not isinstance(
        raw_targets,
        list,
    ):
        return ()

    targets: list[
        SessionGuidanceIntensityTarget
    ] = []

    for raw_target in raw_targets:
        if not isinstance(
            raw_target,
            dict,
        ):
            continue

        reference = raw_target.get(
            "reference"
        )
        label = raw_target.get(
            "label"
        )
        minimum = raw_target.get(
            "minimum"
        )
        maximum = raw_target.get(
            "maximum"
        )
        unit = raw_target.get(
            "unit"
        )

        if (
            not isinstance(reference, str)
            or not isinstance(label, str)
            or not isinstance(
                minimum,
                (int, float),
            )
            or not isinstance(
                maximum,
                (int, float),
            )
            or not isinstance(unit, str)
        ):
            continue

        speed_min_kmh = None
        speed_max_kmh = None

        pace_fastest = None
        pace_slowest = None

        derived = raw_target.get(
            "derived"
        )

        if isinstance(
            derived,
            dict,
        ):
            speed = derived.get(
                "speed_kmh"
            )

            if isinstance(
                speed,
                dict,
            ):
                raw_minimum = speed.get(
                    "minimum"
                )
                raw_maximum = speed.get(
                    "maximum"
                )

                if isinstance(
                    raw_minimum,
                    (int, float),
                ):
                    speed_min_kmh = float(
                        raw_minimum
                    )

                if isinstance(
                    raw_maximum,
                    (int, float),
                ):
                    speed_max_kmh = float(
                        raw_maximum
                    )

            pace = derived.get(
                "pace_seconds_per_km"
            )

            if isinstance(
                pace,
                dict,
            ):
                raw_fastest = pace.get(
                    "fastest"
                )
                raw_slowest = pace.get(
                    "slowest"
                )

                if isinstance(
                    raw_fastest,
                    (int, float),
                ):
                    pace_fastest = float(
                        raw_fastest
                    )

                if isinstance(
                    raw_slowest,
                    (int, float),
                ):
                    pace_slowest = float(
                        raw_slowest
                    )

        targets.append(
            SessionGuidanceIntensityTarget(
                reference=reference,
                label=label,
                minimum=float(
                    minimum
                ),
                maximum=float(
                    maximum
                ),
                unit=unit,
                speed_min_kmh=(
                    speed_min_kmh
                ),
                speed_max_kmh=(
                    speed_max_kmh
                ),
                pace_fastest_seconds_per_km=(
                    pace_fastest
                ),
                pace_slowest_seconds_per_km=(
                    pace_slowest
                ),
            )
        )

    return tuple(
        targets
    )


def _build_structured_main_step(
    session: TrainingSession,
    *,
    fallback_title: str,
    fallback_description: str,
) -> SessionGuidanceStep | None:
    """Construit un bloc principal depuis la prescription persistée."""

    prescription = session.prescription

    if not isinstance(
        prescription,
        dict,
    ):
        return None

    structure = prescription.get(
        "work_structure"
    )

    if not isinstance(
        structure,
        dict,
    ):
        return None

    intervals = structure.get(
        "intervals"
    )

    if (
        isinstance(
            intervals,
            list,
        )
        and intervals
    ):
        interval = intervals[0]

        if not isinstance(
            interval,
            dict,
        ):
            return None

        repetitions = interval.get(
            "repetitions"
        )

        work_distance = interval.get(
            "work_distance_meters"
        )

        target = interval.get(
            "repetition_target"
        )

        fast_seconds = None
        slow_seconds = None

        if isinstance(
            target,
            dict,
        ):
            raw_fast = target.get(
                "fast_seconds"
            )
            raw_slow = target.get(
                "slow_seconds"
            )

            if isinstance(
                raw_fast,
                (int, float),
            ):
                fast_seconds = float(
                    raw_fast
                )

            if isinstance(
                raw_slow,
                (int, float),
            ):
                slow_seconds = float(
                    raw_slow
                )

        recovery_description = (
            _format_recovery(
                interval
            )
        )

        title = fallback_title

        if (
            isinstance(
                repetitions,
                int,
            )
            and repetitions > 0
            and isinstance(
                work_distance,
                int,
            )
            and work_distance > 0
        ):
            title = (
                f"{repetitions} × "
                f"{work_distance} m"
            )

        return SessionGuidanceStep(
            title=title,
            description=(
                structure.get(
                    "description"
                )
                or fallback_description
            ),
            duration_minutes=None,
            intensity_target=(
                session.intensity
                or None
            ),
            heart_rate_target=(
                session.heart_rate_zone
            ),
            intensity_targets=(
                _build_intensity_targets(
                    session
                )
            ),
            repetitions=(
                repetitions
                if isinstance(
                    repetitions,
                    int,
                )
                else None
            ),
            work_distance_meters=(
                work_distance
                if isinstance(
                    work_distance,
                    int,
                )
                else None
            ),
            repetition_fast_seconds=(
                fast_seconds
            ),
            repetition_slow_seconds=(
                slow_seconds
            ),
            recovery_description=(
                recovery_description
            ),
        )

    return None


def _format_recovery(
    interval: dict,
) -> str | None:
    duration = interval.get(
        "recovery_duration"
    )

    unit = interval.get(
        "recovery_unit"
    )

    if not isinstance(
        duration,
        (int, float),
    ):
        return None

    if unit == "seconds":
        return (
            f"{int(duration)} s"
        )

    if unit == "minutes":
        return (
            f"{duration:g} min"
        )

    if isinstance(
        unit,
        str,
    ):
        return (
            f"{duration:g} {unit}"
        )

    return None


def _main_session_step(
    session: TrainingSession,
    *,
    fallback_title: str,
    fallback_description: str,
) -> SessionGuidanceStep:
    """Conserve les consignes spécifiques déjà générées."""

    structured = (
        _build_structured_main_step(
            session,
            fallback_title=(
                fallback_title
            ),
            fallback_description=(
                fallback_description
            ),
        )
    )

    if structured is not None:
        return structured

    description = (
        session.description.strip()
        or fallback_description
    )

    return SessionGuidanceStep(
        title=fallback_title,
        description=description,
        duration_minutes=(
            session.duration_minutes
        ),
        intensity_target=(
            session.intensity
            or None
        ),
        heart_rate_target=(
            session.heart_rate_zone
        ),
        intensity_targets=(
            _build_intensity_targets(
                session
            )
        ),
    )


def _build_aerobic_easy(
    session: TrainingSession,
) -> SessionGuidance:
    return SessionGuidance(
        session_type=session.type,
        objective=(
            "Développer l'endurance aérobie tout en maintenant "
            "une charge physiologique faible."
        ),
        coach_rationale=(
            "Cette séance construit la base d'endurance, favorise "
            "la récupération entre les séances de qualité et permet "
            "d'accumuler du volume sans fatigue excessive."
        ),
        terrain_recommendation=(
            "Terrain facile et régulier. Une légère variation de relief "
            "est acceptable tant qu'elle ne transforme pas la séance "
            "en travail d'intensité."
        ),
        preparation=(
            "Partir suffisamment hydraté.",
            (
                "Choisir une allure qui permet de courir relâché "
                "dès les premières minutes."
            ),
        ),
        warmup=(
            SessionGuidanceStep(
                title="Mise en route",
                description=(
                    "Commencer très facilement puis laisser "
                    "l'allure augmenter naturellement."
                ),
                duration_minutes=10,
                intensity_target="très facile",
            ),
        ),
        main_set=(
            _main_session_step(
                session,
                fallback_title="Endurance facile",
                fallback_description=(
                    "Courir à une intensité confortable et stable. "
                    "La respiration doit rester contrôlée et "
                    "la sensation d'effort modérée."
                ),
            ),
        ),
        cooldown=(
            SessionGuidanceStep(
                title="Fin de séance",
                description=(
                    "Terminer les dernières minutes tranquillement "
                    "sans chercher à accélérer."
                ),
                duration_minutes=5,
                intensity_target="très facile",
            ),
        ),
        execution_advice=(
            (
                "L'objectif n'est pas de battre une allure moyenne "
                "mais de respecter une faible intensité."
            ),
            (
                "Ralentir dans les montées si nécessaire pour "
                "conserver la cible physiologique."
            ),
        ),
        warnings=(
            (
                "Éviter de transformer la fin de séance "
                "en tempo ou en compétition."
            ),
        ),
        analysis_targets=(
            "duration",
            "distance",
            "pace",
            "heart_rate",
            "heart_rate_drift",
            "elevation_gain",
        ),
    )


def _build_long_endurance(
    session: TrainingSession,
) -> SessionGuidance:
    return SessionGuidance(
        session_type=session.type,
        objective=(
            "Développer l'endurance prolongée et la capacité "
            "à maintenir un effort durable."
        ),
        coach_rationale=(
            "La sortie longue prépare l'organisme à soutenir un effort "
            "sur une durée importante et développe la résistance "
            "musculaire, énergétique et mentale."
        ),
        terrain_recommendation=(
            "Terrain représentatif de la pratique de l'athlète. "
            "Pour un trailer, privilégier progressivement le relief "
            "et la technicité utiles à ses objectifs."
        ),
        preparation=(
            (
                "Prévoir hydratation et ravitaillement adaptés "
                "à la durée de la séance."
            ),
            (
                "Vérifier le matériel avant le départ pour éviter "
                "les interruptions inutiles."
            ),
        ),
        warmup=(
            SessionGuidanceStep(
                title="Départ progressif",
                description=(
                    "Les premières minutes doivent être particulièrement "
                    "faciles afin de laisser l'organisme monter en régime."
                ),
                duration_minutes=15,
                intensity_target="facile",
            ),
        ),
        main_set=(
            _main_session_step(
                session,
                fallback_title="Sortie longue",
                fallback_description=(
                    "Maintenir un effort durable et contrôlé pendant "
                    "l'ensemble de la sortie."
                ),
            ),
        ),
        cooldown=(
            SessionGuidanceStep(
                title="Retour au calme",
                description=(
                    "Réduire progressivement l'intensité "
                    "sur la fin de la sortie."
                ),
                duration_minutes=5,
                intensity_target="très facile",
            ),
        ),
        execution_advice=(
            (
                "Commencer volontairement en retenue : "
                "la qualité de la seconde moitié compte davantage."
            ),
            (
                "Sur terrain vallonné, raisonner en intensité "
                "plutôt qu'en allure instantanée."
            ),
            (
                "Tester la stratégie d'hydratation et de nutrition "
                "lorsque la durée le justifie."
            ),
        ),
        warnings=(
            "Éviter un départ trop rapide.",
            (
                "Ne pas transformer systématiquement la sortie longue "
                "en séance de haute intensité."
            ),
        ),
        analysis_targets=(
            "duration",
            "distance",
            "pace",
            "heart_rate",
            "heart_rate_drift",
            "elevation_gain",
            "elevation_loss",
            "nutrition",
        ),
    )


def _build_threshold(
    session: TrainingSession,
) -> SessionGuidance:
    return SessionGuidance(
        session_type=session.type,
        objective=(
            "Améliorer la capacité à soutenir une intensité élevée "
            "proche du seuil sans dérive excessive."
        ),
        coach_rationale=(
            "Le travail au seuil améliore l'endurance à haute intensité "
            "et la capacité à maintenir une allure soutenue de manière "
            "contrôlée."
        ),
        terrain_recommendation=(
            "Terrain régulier, faux-plat léger ou montée stable. "
            "Éviter les interruptions et les variations brutales "
            "qui rendent l'intensité difficile à contrôler."
        ),
        preparation=(
            (
                "Arriver relativement frais afin que la séance "
                "mesure réellement la capacité au seuil."
            ),
        ),
        warmup=(
            SessionGuidanceStep(
                title="Échauffement facile",
                description=(
                    "Course facile et progressive avant le travail "
                    "de qualité."
                ),
                duration_minutes=15,
                intensity_target="facile",
            ),
            SessionGuidanceStep(
                title="Préparation à l'intensité",
                description=(
                    "Quelques accélérations progressives courtes "
                    "pour préparer le passage au seuil."
                ),
                duration_minutes=4,
            ),
        ),
        main_set=(
            _main_session_step(
                session,
                fallback_title="Travail au seuil",
                fallback_description=(
                    "Réaliser le bloc prévu autour de l'intensité seuil "
                    "en recherchant régularité et maîtrise."
                ),
            ),
        ),
        cooldown=(
            SessionGuidanceStep(
                title="Retour au calme",
                description="Course facile après le dernier bloc.",
                duration_minutes=10,
                intensity_target="facile",
            ),
        ),
        execution_advice=(
            (
                "Le premier bloc doit sembler contrôlé. "
                "L'intensité doit devenir exigeante progressivement."
            ),
            (
                "Chercher une intensité régulière plutôt que "
                "des variations d'allure importantes."
            ),
        ),
        warnings=(
            (
                "Un départ trop rapide peut transformer le travail "
                "au seuil en effort VO2max."
            ),
            (
                "Ne pas chercher systématiquement une fréquence "
                "cardiaque cible dès les premières minutes du bloc."
            ),
        ),
        analysis_targets=(
            "pace",
            "speed",
            "heart_rate",
            "heart_rate_drift",
            "interval_consistency",
            "recovery",
            "elevation_gain",
        ),
    )


def _build_vo2max(
    session: TrainingSession,
) -> SessionGuidance:
    return SessionGuidance(
        session_type=session.type,
        objective=(
            "Développer la puissance aérobie et la capacité "
            "à soutenir des intensités proches de la VMA."
        ),
        coach_rationale=(
            "Les répétitions à haute intensité sollicitent fortement "
            "le système aérobie et permettent de développer "
            "la puissance maximale utilisable en course."
        ),
        terrain_recommendation=(
            "Piste, route plate, faux-plat régulier ou montée constante "
            "selon le format prescrit."
        ),
        preparation=(
            (
                "Cette séance doit idéalement être réalisée avec "
                "un niveau de fraîcheur suffisant."
            ),
        ),
        warmup=(
            SessionGuidanceStep(
                title="Échauffement",
                description=(
                    "Course facile progressive avant les répétitions."
                ),
                duration_minutes=15,
                intensity_target="facile",
            ),
            SessionGuidanceStep(
                title="Accélérations",
                description=(
                    "3 à 4 accélérations progressives courtes "
                    "avec récupération complète."
                ),
                duration_minutes=5,
            ),
        ),
        main_set=(
            _main_session_step(
                session,
                fallback_title="Bloc VO2max",
                fallback_description=(
                    "Réaliser les répétitions prévues à haute intensité "
                    "en conservant une exécution régulière."
                ),
            ),
        ),
        cooldown=(
            SessionGuidanceStep(
                title="Retour au calme",
                description="Course très facile.",
                duration_minutes=10,
                intensity_target="facile",
            ),
        ),
        execution_advice=(
            (
                "La première répétition ne doit pas être "
                "la plus rapide de toute la séance."
            ),
            (
                "Chercher à conserver une qualité similaire "
                "sur l'ensemble des répétitions."
            ),
        ),
        warnings=(
            "Éviter les départs en sprint.",
            (
                "Si l'allure s'effondre fortement, la cible initiale "
                "était probablement trop ambitieuse."
            ),
        ),
        analysis_targets=(
            "pace",
            "speed",
            "heart_rate",
            "max_heart_rate",
            "interval_consistency",
            "recovery",
            "cadence",
        ),
    )


def _build_speed_development(
    session: TrainingSession,
) -> SessionGuidance:
    return SessionGuidance(
        session_type=session.type,
        objective=(
            "Développer la vitesse, l'économie de course "
            "et la qualité gestuelle à haute allure."
        ),
        coach_rationale=(
            "Le travail de vitesse améliore la coordination "
            "neuromusculaire et permet de courir vite sans accumuler "
            "nécessairement une forte fatigue métabolique."
        ),
        terrain_recommendation=(
            "Surface régulière, sûre et suffisamment plate. "
            "Une piste est idéale pour les répétitions mesurées."
        ),
        preparation=(
            (
                "Prendre le temps de s'échauffer : "
                "la vitesse nécessite des muscles bien préparés."
            ),
        ),
        warmup=(
            SessionGuidanceStep(
                title="Course facile",
                description="Échauffement progressif.",
                duration_minutes=15,
                intensity_target="facile",
            ),
            SessionGuidanceStep(
                title="Éducatifs et accélérations",
                description=(
                    "Préparer progressivement la foulée "
                    "avant les efforts rapides."
                ),
                duration_minutes=8,
            ),
        ),
        main_set=(
            _main_session_step(
                session,
                fallback_title="Développement de la vitesse",
                fallback_description=(
                    "Réaliser les répétitions rapides avec une foulée "
                    "relâchée, dynamique et techniquement propre."
                ),
            ),
        ),
        cooldown=(
            SessionGuidanceStep(
                title="Retour au calme",
                description="Course très facile.",
                duration_minutes=10,
                intensity_target="facile",
            ),
        ),
        execution_advice=(
            "Privilégier la qualité à la quantité.",
            (
                "Chercher vitesse et relâchement plutôt qu'un effort "
                "désordonné à intensité maximale."
            ),
        ),
        warnings=(
            (
                "Arrêter les répétitions rapides si la technique "
                "se dégrade fortement."
            ),
        ),
        analysis_targets=(
            "pace",
            "speed",
            "cadence",
            "interval_consistency",
            "recovery",
        ),
    )


def _build_strength_lower_body(
    session: TrainingSession,
) -> SessionGuidance:
    return SessionGuidance(
        session_type=session.type,
        objective=(
            "Renforcer les membres inférieurs et améliorer "
            "la robustesse nécessaire à la course."
        ),
        coach_rationale=(
            "Le renforcement contribue à la tolérance mécanique, "
            "à la stabilité et à l'économie de mouvement."
        ),
        terrain_recommendation=(
            "Espace stable et sécurisé permettant d'exécuter "
            "les mouvements avec contrôle."
        ),
        preparation=(
            (
                "Préparer les articulations avec quelques mouvements "
                "dynamiques avant les exercices chargés."
            ),
        ),
        warmup=(
            SessionGuidanceStep(
                title="Mobilité dynamique",
                description=(
                    "Mobiliser chevilles, genoux, hanches "
                    "et chaîne postérieure."
                ),
                duration_minutes=8,
            ),
        ),
        main_set=(
            _main_session_step(
                session,
                fallback_title="Renforcement membres inférieurs",
                fallback_description=(
                    "Exécuter les exercices prévus avec contrôle, "
                    "amplitude adaptée et technique stable."
                ),
            ),
        ),
        cooldown=(),
        execution_advice=(
            (
                "Conserver une exécution propre avant de chercher "
                "à augmenter la charge ou le nombre de répétitions."
            ),
        ),
        warnings=(
            (
                "Une douleur articulaire aiguë n'est pas "
                "un objectif normal du renforcement."
            ),
        ),
        analysis_targets=(
            "duration",
            "completion",
            "perceived_effort",
        ),
    )


def _build_rest(
    session: TrainingSession,
) -> SessionGuidance:
    return SessionGuidance(
        session_type=session.type,
        objective="Permettre l'assimilation de l'entraînement.",
        coach_rationale=(
            "La récupération fait partie du programme. "
            "Elle permet de transformer la charge d'entraînement "
            "en adaptation."
        ),
        terrain_recommendation="Aucun terrain spécifique.",
        preparation=(),
        warmup=(),
        main_set=(
            SessionGuidanceStep(
                title="Récupération",
                description=(
                    "Repos ou activité très légère selon les sensations."
                ),
            ),
        ),
        cooldown=(),
        execution_advice=(
            "Privilégier sommeil, hydratation et récupération.",
        ),
        warnings=(
            (
                "Éviter de remplacer spontanément le repos "
                "par une séance intense."
            ),
        ),
        analysis_targets=(
            "wellness",
            "fatigue",
            "sleep",
        ),
    )


def _build_supplementary(
    session: TrainingSession,
) -> SessionGuidance:
    return SessionGuidance(
        session_type=session.type,
        objective=(
            "Documenter une activité supplémentaire réalisée "
            "en dehors de la planification principale."
        ),
        coach_rationale=(
            "OpenCoach prend cette activité en compte pour comprendre "
            "la charge totale réellement réalisée."
        ),
        terrain_recommendation="Selon l'activité réalisée.",
        preparation=(),
        warmup=(),
        main_set=(
            _main_session_step(
                session,
                fallback_title=session.title,
                fallback_description=(
                    "Activité supplémentaire enregistrée."
                ),
            ),
        ),
        cooldown=(),
        execution_advice=(),
        warnings=(
            (
                "Une activité supplémentaire augmente la charge "
                "même lorsqu'elle n'était pas prévue."
            ),
        ),
        analysis_targets=(
            "duration",
            "distance",
            "training_load",
            "heart_rate",
        ),
    )


def _build_generic(
    session: TrainingSession,
) -> SessionGuidance:
    """Fallback pour les futurs types encore non documentés."""

    return SessionGuidance(
        session_type=session.type,
        objective=(
            session.title
            or "Réaliser la séance planifiée."
        ),
        coach_rationale=(
            "Cette séance fait partie de la progression "
            "construite par OpenCoach."
        ),
        terrain_recommendation=(
            "Choisir un environnement compatible avec "
            "les consignes de la séance."
        ),
        preparation=(),
        warmup=(),
        main_set=(
            _main_session_step(
                session,
                fallback_title=session.title,
                fallback_description=(
                    "Respecter les consignes prévues "
                    "pour cette séance."
                ),
            ),
        ),
        cooldown=(),
        execution_advice=(
            "Privilégier la qualité d'exécution.",
        ),
        warnings=(),
        analysis_targets=(
            "duration",
            "distance",
            "heart_rate",
        ),
    )
