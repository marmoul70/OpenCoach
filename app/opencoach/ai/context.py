"""Construction d'un contexte sportif minimal, déterministe et en lecture seule."""

from __future__ import annotations

from opencoach.planning.context import PlanningContext


def build_athlete_context(context: PlanningContext) -> str:
    """Transforme le contexte métier OpenCoach en faits lisibles par l'IA.

    Les données personnelles directes, notes libres et coordonnées sont exclues.
    Cette fonction ne calcule aucune décision et ne modifie aucune donnée.
    """
    athlete = context.athlete
    training = athlete.training
    physiology = athlete.physiology
    lines = [
        "CONTEXTE SPORTIF OPENCOACH — faits calculés par les services métier.",
        f"Date de référence : {context.planning_date.isoformat()}.",
    ]

    if training.sport_disciplines:
        lines.append(
            "Disciplines : " + ", ".join(training.sport_disciplines) + "."
        )
    if training.experience:
        lines.append(f"Niveau déclaré : {training.experience}.")
    if training.weekly_sessions is not None:
        lines.append(f"Objectif hebdomadaire : {training.weekly_sessions} séances.")
    if training.weekly_duration_minutes is not None:
        lines.append(
            "Durée hebdomadaire de référence : "
            f"{training.weekly_duration_minutes} minutes."
        )
    if training.weekly_distance_km is not None:
        lines.append(
            f"Distance hebdomadaire de référence : {training.weekly_distance_km:.1f} km."
        )
    if physiology.vma is not None:
        lines.append(f"VMA enregistrée : {physiology.vma:.1f} km/h.")
    if physiology.max_heart_rate is not None:
        lines.append(f"Fréquence cardiaque maximale enregistrée : {physiology.max_heart_rate} bpm.")
    if physiology.resting_heart_rate is not None:
        lines.append(
            "Fréquence cardiaque au repos enregistrée : "
            f"{physiology.resting_heart_rate} bpm."
        )

    stats = context.recent_stats
    if stats is not None:
        lines.append(
            f"Entraînement réalisé sur la période {stats.start_date.isoformat()} "
            f"au {stats.end_date.isoformat()} : {stats.sessions_count} séances, "
            f"{stats.total_duration_minutes} minutes, "
            f"{stats.total_distance_km:.1f} km, "
            f"{stats.total_elevation_gain_m:.0f} m D+."
        )
        lines.append(
            f"Charge réelle cumulée : {stats.total_load:.1f} "
            "(mesurée + estimée)."
        )

    load = context.recent_load
    if load is not None:
        lines.append(
            f"Charge récente comparée au plan : {load.analyzed_days} jours analysés, "
            f"{load.above_plan_days} au-dessus, {load.on_plan_days} dans le plan, "
            f"{load.below_plan_days} en dessous."
        )
        lines.append(
            f"Couverture du planning : {load.planning_coverage_ratio:.0%}."
        )

    readiness = context.readiness
    if readiness is not None:
        lines.append(
            f"Disponibilité quotidienne calculée : {readiness.readiness.level} "
            f"(score {readiness.readiness.score:.0f}/100), "
            f"données {readiness.data_status} du {readiness.source_date.isoformat()} "
            f"(source : {readiness.provider})."
        )
        if readiness.readiness.training_constraints:
            lines.append(
                "Restrictions calculées : "
                + ", ".join(readiness.readiness.training_constraints)
                + "."
            )
    else:
        lines.append("Disponibilité quotidienne : aucune donnée exploitable.")

    race = context.primary_race
    if race is not None:
        lines.append(
            f"Prochaine course principale : {race.name}, "
            f"le {race.date.isoformat()}, {race.distance_km:.1f} km, "
            f"{(race.elevation_gain_m or 0):.0f} m D+."
        )
    else:
        lines.append("Aucune course principale future enregistrée.")

    active_constraints = [
        item for item in context.constraints
        if item.is_active_on(context.planning_date)
    ]
    if active_constraints:
        lines.append(
            "Contraintes actives : "
            + "; ".join(
                f"{item.constraint_type} ({item.availability}, "
                f"du {item.start_date.isoformat()} au {item.end_date.isoformat()})"
                for item in active_constraints
            )
            + "."
        )
    else:
        lines.append("Aucune contrainte temporaire active à la date de référence.")

    lines.extend([
        "Règles d'interprétation : ces faits peuvent être incomplets ou datés.",
        "Ne déduis pas de données absentes. Les décisions d'entraînement restent "
        "du ressort des services déterministes OpenCoach.",
        "Tu ne peux modifier ni séance, ni planning, ni activité, ni donnée COROS.",
    ])
    return "\n".join(lines)
