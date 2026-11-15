"""Contexte physiologique et capacité d'entraînement du profil athlète.

Ce service prépare une vue métier stable du profil pour les consommateurs
Coach (API, interface et adaptateurs conversationnels).
"""
from __future__ import annotations

from opencoach.models import AthletePhysiology, HeartRateZone, HeartRateZones
from opencoach.physiology.heart_rate_zones import get_heart_rate_zone
from opencoach.services.profile import ProfileService


class TrainingProfileContextService:
    """Construit le contexte d'entraînement à partir du profil canonique."""

    def __init__(self, profile_service: ProfileService) -> None:
        self.profile_service = profile_service

    def build(self) -> dict:
        profile = self.profile_service.get_profile()
        if profile is None:
            return {
                "status": "unavailable",
                "message": "Le profil sportif de cet athlète est introuvable.",
            }

        raw_zones = profile.physiology.heart_rate_zones or {}
        zone_values = {}
        for name in ("z1", "z2", "z3", "z4", "z5"):
            raw_zone = (
                raw_zones.get(name)
                if isinstance(raw_zones, dict)
                else getattr(raw_zones, name, None)
            )
            try:
                raw_max_bpm = (
                    raw_zone.get("max_bpm")
                    if isinstance(raw_zone, dict)
                    else getattr(raw_zone, "max_bpm", None)
                )
                max_bpm = int(raw_max_bpm) if raw_max_bpm is not None else None
            except (TypeError, ValueError):
                max_bpm = None
            zone_values[name] = (
                HeartRateZone(max_bpm=max_bpm)
                if max_bpm is not None and max_bpm > 0
                else None
            )

        physiology = AthletePhysiology(
            max_heart_rate=profile.physiology.max_heart_rate,
            resting_heart_rate=profile.physiology.resting_heart_rate,
            vma=profile.physiology.vma,
            threshold_heart_rate_1=profile.physiology.threshold_heart_rate_1,
            threshold_heart_rate_2=profile.physiology.threshold_heart_rate_2,
            heart_rate_zones=HeartRateZones(**zone_values),
        )

        heart_rate_zones = []
        invalid_zone_order = False
        for name in ("z1", "z2", "z3", "z4", "z5"):
            prescription = get_heart_rate_zone(physiology, name)
            if prescription is None:
                continue
            if (
                prescription.min_bpm is not None
                and prescription.min_bpm > prescription.max_bpm
            ):
                invalid_zone_order = True
            heart_rate_zones.append(
                {
                    "zone": prescription.zone,
                    "min_bpm": prescription.min_bpm,
                    "max_bpm": prescription.max_bpm,
                }
            )

        missing = [
            name
            for name, value in (
                ("vma", profile.physiology.vma),
                ("max_heart_rate", profile.physiology.max_heart_rate),
                ("threshold_heart_rate_1", profile.physiology.threshold_heart_rate_1),
                ("threshold_heart_rate_2", profile.physiology.threshold_heart_rate_2),
            )
            if value is None
        ]
        if not heart_rate_zones:
            missing.append("heart_rate_zones")
        elif len(heart_rate_zones) < 5:
            missing.append("heart_rate_zones_incomplete")

        return {
            "status": "partial" if missing else "ok",
            "physiology": {
                "vma_kmh": profile.physiology.vma,
                "max_heart_rate_bpm": profile.physiology.max_heart_rate,
                "resting_heart_rate_bpm": profile.physiology.resting_heart_rate,
                "threshold_heart_rate_1_bpm": profile.physiology.threshold_heart_rate_1,
                "threshold_heart_rate_2_bpm": profile.physiology.threshold_heart_rate_2,
                "heart_rate_zones": heart_rate_zones,
                "heart_rate_zones_order_valid": not invalid_zone_order,
            },
            "training_capacity": {
                "experience": profile.training.experience,
                "sport_disciplines": list(profile.training.sport_disciplines or []),
                "weekly_sessions_target": profile.training.weekly_sessions,
                "weekly_duration_target_minutes": profile.training.weekly_duration_minutes,
                "weekly_distance_target_km": profile.training.weekly_distance_km,
                "available_days": list(profile.training.available_days or []),
                "fatigue_threshold": profile.training.fatigue_threshold,
            },
            "fueling_targets": {
                "carbohydrates_g_per_hour": profile.nutrition.carbohydrates_per_hour,
                "fluids_per_hour": profile.nutrition.fluids_per_hour,
                "sodium_per_hour": profile.nutrition.sodium_per_hour,
            },
            "missing_profile_fields": missing,
            "interpretation_rules": [
                "Les valeurs absentes ne sont pas estimées.",
                "Ne pas calculer de zones d'allure à partir de la VMA sans outil dédié.",
                "Si l'ordre des zones cardiaques est invalide, demander une correction du profil avant de prescrire une intensité en bpm.",
            ],
        }
