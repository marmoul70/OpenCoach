"""Messages de débriefing déterministes."""

from __future__ import annotations

from .models import (
    GoalComplianceStatus,
    GoalMetricAssessment,
    GoalType,
)


def build_metric_message(
    metric: GoalMetricAssessment,
) -> str:
    """Produit une observation courte et actionnable."""

    if metric.status is GoalComplianceStatus.NOT_USED:
        return (
            f"{metric.label} : indicateur informatif, "
            "non utilisé pour déterminer la conformité "
            "de cette séance."
        )

    if metric.key == "time_in_heart_rate_target":
        return _zone_message(
            metric,
            label="zone cardiaque cible",
        )

    if metric.key == "time_in_pace_target":
        return _zone_message(
            metric,
            label="allure cible",
        )

    if metric.key == "work_duration":
        return _work_duration_message(
            metric
        )

    if metric.key == "repetition_count":
        return _repetition_count_message(
            metric
        )

    if metric.key == "recovery_duration":
        return _recovery_message(
            metric
        )

    if metric.key == "duration":
        return _duration_message(
            metric
        )

    return _generic_message(
        metric
    )


def build_session_debriefing(
    *,
    goal_type: GoalType,
    overall_status: GoalComplianceStatus,
    strengths: tuple[str, ...],
    attention_points: tuple[str, ...],
    metrics: tuple[GoalMetricAssessment, ...] = (),
) -> str:
    """Produit le résumé principal du coach."""

    if (
        goal_type is GoalType.ENDURANCE
        and metrics
    ):
        return _build_endurance_debriefing(
            overall_status=overall_status,
            metrics=metrics,
        )

    if (
        goal_type is GoalType.INTERVALS
        and metrics
    ):
        return _build_intervals_debriefing(
            overall_status=overall_status,
            metrics=metrics,
        )

    if overall_status is GoalComplianceStatus.OK:
        if goal_type is GoalType.ENDURANCE:
            return (
                "La séance respecte l'objectif d'endurance : "
                "l'intensité principale et le volume utile "
                "sont correctement maîtrisés."
            )

        if goal_type is GoalType.INTERVALS:
            return (
                "La séance structurée respecte le stimulus "
                "prévu : les fractions principales ont été "
                "réalisées avec une intensité et une structure "
                "cohérentes avec la prescription."
            )

        if goal_type is GoalType.PHYSIOLOGICAL_TEST:
            return (
                "Le protocole du test est suffisamment "
                "respecté pour exploiter son résultat."
            )

        return (
            "Les éléments principaux de la séance sont "
            "conformes à la prescription."
        )

    if overall_status is GoalComplianceStatus.ATTENTION:
        if attention_points:
            return (
                "La séance est globalement exploitable, mais "
                "un ou plusieurs écarts doivent être corrigés "
                "pour mieux respecter l'objectif du coach."
            )

        return (
            "La séance présente quelques écarts modérés par "
            "rapport à l'objectif prévu."
        )

    if overall_status is GoalComplianceStatus.NON_COMPLIANT:
        return (
            "L'objectif principal de la séance n'a pas été "
            "suffisamment respecté. Le débriefing doit servir "
            "à corriger l'exécution des prochaines séances "
            "de même objectif."
        )

    return (
        "Les données disponibles ne permettent pas "
        "d'utiliser cette analyse pour juger l'objectif."
    )





def _build_endurance_debriefing(
    *,
    overall_status: GoalComplianceStatus,
    metrics: tuple[GoalMetricAssessment, ...],
) -> str:
    """Produit un débriefing chiffré d'une séance d'endurance."""

    values = {
        metric.key: metric
        for metric in metrics
    }

    heart_rate = values.get(
        "time_in_heart_rate_target"
    )

    pace = values.get(
        "time_in_pace_target"
    )

    duration = values.get(
        "duration"
    )

    sentences: list[str] = []

    # --------------------------------------------------------
    # Intensité physiologique principale
    # --------------------------------------------------------

    if (
        heart_rate is not None
        and heart_rate.actual_value is not None
        and heart_rate.status
        is not GoalComplianceStatus.NOT_USED
    ):
        adherence = heart_rate.actual_value

        if (
            heart_rate.status
            is GoalComplianceStatus.OK
        ):
            sentences.append(
                "L'intensité d'endurance a été correctement "
                f"maîtrisée : {adherence:.0f} % du temps actif "
                "a été passé dans la zone cardiaque cible."
            )

        elif (
            heart_rate.status
            is GoalComplianceStatus.ATTENTION
        ):
            sentences.append(
                f"{adherence:.0f} % du temps actif a été passé "
                "dans la zone cardiaque cible. L'intensité est "
                "proche de l'objectif, mais pourrait être mieux "
                "maîtrisée."
            )

        elif (
            heart_rate.status
            is GoalComplianceStatus.NON_COMPLIANT
        ):
            sentences.append(
                f"Seulement {adherence:.0f} % du temps actif "
                "a été passé dans la zone cardiaque cible. "
                "L'intensité d'endurance prévue n'a donc pas "
                "été suffisamment respectée."
            )

    # Une cible d'allure peut remplacer/compléter la FC
    # lorsqu'elle est réellement prescrite.
    elif (
        pace is not None
        and pace.actual_value is not None
        and pace.status
        is not GoalComplianceStatus.NOT_USED
    ):
        adherence = pace.actual_value

        if (
            pace.status
            is GoalComplianceStatus.OK
        ):
            sentences.append(
                f"{adherence:.0f} % du temps actif a été passé "
                "dans l'allure prescrite."
            )

        elif (
            pace.status
            is GoalComplianceStatus.ATTENTION
        ):
            sentences.append(
                f"{adherence:.0f} % du temps actif a été passé "
                "dans l'allure prescrite. L'intensité est "
                "globalement proche de la cible."
            )

        else:
            sentences.append(
                f"Seulement {adherence:.0f} % du temps actif "
                "a été passé dans l'allure prescrite. "
                "L'intensité prévue n'a pas été suffisamment "
                "respectée."
            )

    # --------------------------------------------------------
    # Volume secondaire
    # --------------------------------------------------------

    if (
        duration is not None
        and duration.actual_value is not None
        and duration.target_minimum is not None
    ):
        actual = duration.actual_value

        target = duration.target_minimum

        if (
            duration.status
            is GoalComplianceStatus.OK
        ):
            sentences.append(
                f"La durée prévue est respectée : "
                f"{actual:.0f} min pour "
                f"{target:.0f} min prescrites."
            )

        elif (
            duration.delta is not None
            and duration.delta > 0
        ):
            percentage = (
                duration.delta_percent
            )

            message = (
                f"La séance a duré {actual:.0f} min au lieu "
                f"des {target:.0f} min prescrites"
            )

            if percentage is not None:
                message += (
                    f", soit environ "
                    f"{abs(percentage):.0f} % de plus"
                )

            sentences.append(
                message + "."
            )

        elif (
            duration.delta is not None
            and duration.delta < 0
        ):
            percentage = (
                duration.delta_percent
            )

            message = (
                f"La séance a duré {actual:.0f} min au lieu "
                f"des {target:.0f} min prescrites"
            )

            if percentage is not None:
                message += (
                    f", soit environ "
                    f"{abs(percentage):.0f} % de moins"
                )

            sentences.append(
                message + "."
            )

    # --------------------------------------------------------
    # Conclusion coach
    # --------------------------------------------------------

    if (
        overall_status
        is GoalComplianceStatus.NON_COMPLIANT
    ):
        if (
            heart_rate is not None
            and heart_rate.status
            is GoalComplianceStatus.NON_COMPLIANT
        ):
            sentences.append(
                "Pour une prochaine séance d'endurance facile, "
                "réduis l'intensité lorsque la fréquence "
                "cardiaque dépasse durablement la zone cible ; "
                "en montée, ralentir ou marcher peut être "
                "nécessaire pour préserver le stimulus recherché."
            )

        else:
            sentences.append(
                "Pour la prochaine séance de même objectif, "
                "rapproche l'exécution de la prescription afin "
                "de préserver le stimulus d'endurance recherché."
            )

    elif (
        overall_status
        is GoalComplianceStatus.ATTENTION
    ):
        sentences.append(
            "La séance reste exploitable, mais une meilleure "
            "maîtrise de l'intensité ou du volume permettra de "
            "mieux cibler le stimulus recherché."
        )

    elif (
        overall_status
        is GoalComplianceStatus.OK
    ):
        sentences.append(
            "Le stimulus d'endurance recherché est correctement "
            "respecté."
        )

    if sentences:
        return " ".join(
            sentences
        )

    return (
        "Les données disponibles ne permettent pas de produire "
        "un débriefing suffisamment précis de cette séance "
        "d'endurance."
    )

def _format_pace_from_repetition(
    *,
    duration_seconds: float,
    distance_m: float,
) -> str | None:
    """Convertit un chrono de fraction en allure min/km."""

    if (
        duration_seconds <= 0
        or distance_m <= 0
    ):
        return None

    seconds_per_km = (
        duration_seconds
        * 1000.0
        / distance_m
    )

    minutes = int(
        seconds_per_km // 60
    )

    seconds = int(
        round(
            seconds_per_km
            - minutes * 60
        )
    )

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}'{seconds:02d}/km"


def _build_intervals_debriefing(
    *,
    overall_status: GoalComplianceStatus,
    metrics: tuple[GoalMetricAssessment, ...],
) -> str:
    """Produit un débriefing chiffré d'une séance fractionnée."""

    values = {
        metric.key: metric
        for metric in metrics
    }

    repetition_count = values.get(
        "repetition_count"
    )

    work_duration = values.get(
        "work_duration"
    )

    work_distance = values.get(
        "work_distance"
    )

    recovery = values.get(
        "recovery_duration"
    )

    regularity = values.get(
        "repetition_regularity"
    )

    sentences = []

    # --------------------------------------------------------
    # Structure
    # --------------------------------------------------------

    structure_parts = []

    if (
        repetition_count is not None
        and repetition_count.actual_value is not None
    ):
        actual = int(
            round(
                repetition_count.actual_value
            )
        )

        if repetition_count.target_minimum is not None:
            expected = int(
                round(
                    repetition_count.target_minimum
                )
            )

            structure_parts.append(
                f"{actual}/{expected} répétitions"
            )

        else:
            structure_parts.append(
                f"{actual} répétitions"
            )

    if (
        work_distance is not None
        and work_distance.actual_value is not None
    ):
        structure_parts.append(
            f"{work_distance.actual_value:.0f} m "
            "de moyenne"
        )

    if (
        recovery is not None
        and recovery.actual_value is not None
    ):
        if recovery.target_minimum is not None:
            structure_parts.append(
                f"récupérations de "
                f"{recovery.actual_value:.1f} s "
                f"pour "
                f"{recovery.target_minimum:.0f} s prévues"
            )

        else:
            structure_parts.append(
                f"récupérations de "
                f"{recovery.actual_value:.1f} s"
            )

    if structure_parts:
        sentences.append(
            "Structure de séance : "
            + ", ".join(
                structure_parts
            )
            + "."
        )

    # --------------------------------------------------------
    # Intensité principale
    # --------------------------------------------------------

    if (
        work_duration is not None
        and work_duration.actual_value is not None
    ):
        actual = work_duration.actual_value

        target = None

        if (
            work_duration.target_minimum is not None
            and work_duration.target_maximum is not None
        ):
            target = (
                (
                    work_duration.target_minimum
                    + work_duration.target_maximum
                )
                / 2.0
            )

        elif work_duration.target_minimum is not None:
            target = work_duration.target_minimum

        if target is not None:
            if (
                work_duration.status
                is GoalComplianceStatus.OK
            ):
                sentences.append(
                    f"L'intensité est correctement respectée : "
                    f"{actual:.1f} s de moyenne pour une cible "
                    f"de {target:.1f} s."
                )

            elif (
                work_duration.delta is not None
                and work_duration.delta < 0
            ):
                percentage = (
                    abs(
                        work_duration.delta_percent
                    )
                    if work_duration.delta_percent is not None
                    else None
                )

                actual_pace = None
                target_pace = None

                if (
                    work_distance is not None
                    and work_distance.target_minimum is not None
                    and work_distance.target_minimum > 0
                ):
                    prescribed_distance = (
                        work_distance.target_minimum
                    )

                    actual_pace = _format_pace_from_repetition(
                        duration_seconds=actual,
                        distance_m=prescribed_distance,
                    )

                    target_pace = _format_pace_from_repetition(
                        duration_seconds=target,
                        distance_m=prescribed_distance,
                    )

                if (
                    actual_pace is not None
                    and target_pace is not None
                ):
                    message = (
                        f"Les fractions ont été courues en moyenne "
                        f"à {actual_pace} ({actual:.1f} s) au lieu "
                        f"de {target_pace} ({target:.1f} s)"
                    )

                else:
                    message = (
                        f"Les fractions ont été courues en "
                        f"{actual:.1f} s de moyenne au lieu de "
                        f"{target:.1f} s"
                    )

                if percentage is not None:
                    message += (
                        f", soit environ "
                        f"{percentage:.1f} % trop vite"
                    )

                message += "."

                sentences.append(
                    message
                )

            elif (
                work_duration.delta is not None
                and work_duration.delta > 0
            ):
                percentage = (
                    abs(
                        work_duration.delta_percent
                    )
                    if work_duration.delta_percent is not None
                    else None
                )

                message = (
                    f"Les fractions ont été courues en "
                    f"{actual:.1f} s de moyenne au lieu de "
                    f"{target:.1f} s"
                )

                if percentage is not None:
                    message += (
                        f", soit environ "
                        f"{percentage:.1f} % trop lentement"
                    )

                message += "."

                sentences.append(
                    message
                )

    # --------------------------------------------------------
    # Régularité
    # --------------------------------------------------------

    if (
        regularity is not None
        and regularity.actual_value is not None
    ):
        if (
            regularity.status
            is GoalComplianceStatus.OK
        ):
            sentences.append(
                "La série est régulière."
            )

        elif (
            regularity.status
            is GoalComplianceStatus.ATTENTION
        ):
            sentences.append(
                f"La régularité est légèrement perfectible "
                f"({regularity.actual_value:.1f} % de dispersion)."
            )

        elif (
            regularity.status
            is GoalComplianceStatus.NON_COMPLIANT
        ):
            sentences.append(
                f"La série manque de régularité "
                f"({regularity.actual_value:.1f} % de dispersion)."
            )

    # --------------------------------------------------------
    # Conseil
    # --------------------------------------------------------

    if (
        work_duration is not None
        and work_duration.status
        is GoalComplianceStatus.NON_COMPLIANT
        and work_duration.delta is not None
    ):
        if work_duration.delta < 0:
            sentences.append(
                "Pour la prochaine séance de même objectif, "
                "ralentir les répétitions et se rapprocher de "
                "l'intensité prescrite : courir plus vite ne "
                "produit pas nécessairement le stimulus recherché."
            )

        elif work_duration.delta > 0:
            sentences.append(
                "Pour la prochaine séance de même objectif, "
                "augmenter légèrement l'intensité afin de se "
                "rapprocher de la cible prescrite."
            )

    elif overall_status is GoalComplianceStatus.OK:
        sentences.append(
            "La séance peut être considérée comme correctement "
            "exécutée par rapport au stimulus prévu."
        )

    elif overall_status is GoalComplianceStatus.ATTENTION:
        sentences.append(
            "La séance reste globalement exploitable, mais les "
            "écarts signalés sont à corriger lors de la prochaine "
            "séance de même objectif."
        )

    return " ".join(
        sentences
    )

def _zone_message(
    metric: GoalMetricAssessment,
    *,
    label: str,
) -> str:
    if metric.actual_value is None:
        return (
            f"Le temps dans la {label} "
            "n'est pas exploitable."
        )

    value = metric.actual_value

    if metric.status is GoalComplianceStatus.OK:
        return (
            f"{value:.0f} % du temps a été passé dans la "
            f"{label} : objectif correctement maîtrisé."
        )

    if metric.status is GoalComplianceStatus.ATTENTION:
        return (
            f"{value:.0f} % du temps a été passé dans la "
            f"{label}. L'intensité peut être mieux maîtrisée."
        )

    return (
        f"Seulement {value:.0f} % du temps a été passé "
        f"dans la {label}. L'intensité de la séance "
        "n'a pas respecté l'objectif prévu."
    )


def _work_duration_message(
    metric: GoalMetricAssessment,
) -> str:
    if metric.actual_value is None:
        return (
            "Le chrono des répétitions n'est pas exploitable."
        )

    if metric.status is GoalComplianceStatus.OK:
        return (
            "L'allure des répétitions correspond à "
            "l'intensité prescrite."
        )

    if metric.delta is not None:
        if metric.delta < 0:
            return (
                "Les répétitions ont été réalisées trop "
                "rapidement par rapport à l'intensité "
                "prescrite. Plus vite ne signifie pas "
                "nécessairement mieux pour ce stimulus."
            )

        if metric.delta > 0:
            return (
                "Les répétitions ont été réalisées trop "
                "lentement par rapport à l'intensité "
                "prescrite."
            )

    return (
        "L'allure des répétitions s'écarte de "
        "l'intensité prescrite."
    )


def _repetition_count_message(
    metric: GoalMetricAssessment,
) -> str:
    if metric.actual_value is None:
        return (
            "Le nombre de répétitions réalisées "
            "n'est pas exploitable."
        )

    actual = int(
        round(metric.actual_value)
    )

    if metric.target_minimum is not None:
        expected = int(
            round(
                metric.target_minimum
            )
        )

        if metric.status is GoalComplianceStatus.OK:
            return (
                f"Les {actual} répétitions prévues "
                "ont été réalisées."
            )

        return (
            f"{actual} répétition(s) réalisée(s) "
            f"sur {expected} prévue(s)."
        )

    return (
        f"{actual} répétition(s) détectée(s)."
    )


def _recovery_message(
    metric: GoalMetricAssessment,
) -> str:
    if metric.status is GoalComplianceStatus.OK:
        return (
            "Les temps de récupération sont cohérents "
            "avec la prescription."
        )

    if metric.delta is not None:
        if metric.delta < 0:
            return (
                "Les récupérations ont été plus courtes "
                "que prévu."
            )

        if metric.delta > 0:
            return (
                "Les récupérations ont été plus longues "
                "que prévu."
            )

    return (
        "Les récupérations s'écartent de la prescription."
    )


def _duration_message(
    metric: GoalMetricAssessment,
) -> str:
    if metric.status is GoalComplianceStatus.OK:
        return (
            "La durée prescrite a été correctement respectée."
        )

    if metric.delta is not None:
        if metric.delta < 0:
            return (
                "La séance a été plus courte que prévu."
            )

        if metric.delta > 0:
            return (
                "La séance a été plus longue que prévu."
            )

    return (
        "La durée réalisée s'écarte de la prescription."
    )


def _generic_message(
    metric: GoalMetricAssessment,
) -> str:
    if metric.status is GoalComplianceStatus.OK:
        return (
            f"{metric.label} : objectif respecté."
        )

    if metric.status is GoalComplianceStatus.ATTENTION:
        return (
            f"{metric.label} : écart modéré "
            "par rapport à l'objectif."
        )

    return (
        f"{metric.label} : écart important "
        "par rapport à l'objectif."
    )
