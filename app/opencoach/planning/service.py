from datetime import date, timedelta
from uuid import UUID

from opencoach.database.repositories import (
    AthleteConstraintRepository,
    RaceRepository,
    WeeklyTrainingPlanRepository,
)
from opencoach.models import (
    AthleteConstraint,
    Race,
)
from opencoach.readiness import (
    ReadinessAssessment,
    ReadinessDataUnavailableError,
    ReadinessService,
)
from opencoach.services import ProfileService
from opencoach.training import (
    RecentTrainingLoad,
    RecentTrainingLoadService,
    TrainingStats,
    TrainingStatsService,
)

from .context import PlanningContext



CONSTRAINT_HISTORY_DAYS = 7

class PlanningContextService:
    """Construit le contexte consolidé utilisé par le moteur de planification."""

    def __init__(
        self,
        profile_service: ProfileService,
        race_repository: RaceRepository,
        readiness_service: ReadinessService,
        recent_load_service: RecentTrainingLoadService,
        training_stats_service: TrainingStatsService,
        constraint_repository: AthleteConstraintRepository,
        weekly_plan_repository: WeeklyTrainingPlanRepository | None = None,
        *,
        reference_date_provider=date.today,
    ) -> None:
        self.profile_service = profile_service
        self.race_repository = race_repository
        self.readiness_service = readiness_service
        self.recent_load_service = recent_load_service
        self.training_stats_service = training_stats_service
        self.constraint_repository = constraint_repository
        self.weekly_plan_repository = weekly_plan_repository
        self.reference_date_provider = reference_date_provider

    def build(
        self,
        athlete_profile_id: UUID,
        planning_date: date,
        *,
        stats_days: int = 28,
        recent_load_days: int = 7,
        constraint_days: int = 14,
    ) -> PlanningContext:
        """Construit un snapshot des données utiles à la planification."""

        if stats_days < 1:
            raise ValueError(
                "La période de statistiques doit contenir au moins un jour."
            )

        if recent_load_days < 1:
            raise ValueError(
                "La période de charge récente doit contenir au moins un jour."
            )

        if constraint_days < 1:
            raise ValueError(
                "La période de contraintes doit contenir au moins un jour."
            )

        athlete = self.profile_service.get_profile()

        primary_race = (
            self.race_repository.get_next_primary_race(
                athlete_profile_id,
                planning_date,
            )
        )

        training_races = self._get_training_races(
            athlete_profile_id=athlete_profile_id,
            planning_date=planning_date,
            primary_race=primary_race,
        )

        readiness = self._get_readiness(
            athlete_profile_id=athlete_profile_id,
            planning_date=planning_date,
        )

        recent_load = self._get_recent_load(
            athlete_profile_id=athlete_profile_id,
            planning_date=planning_date,
            days=recent_load_days,
        )

        recent_stats = self._get_recent_stats(
            athlete_profile_id=athlete_profile_id,
            planning_date=planning_date,
            days=stats_days,
        )

        constraints_end_date = (
            planning_date
            + timedelta(
                days=constraint_days - 1,
            )
        )

        constraints_start_date = (
            planning_date
            - timedelta(
                days=CONSTRAINT_HISTORY_DAYS
            )
        )

        constraints = self._get_constraints(
            athlete_profile_id=athlete_profile_id,
            start_date=constraints_start_date,
            end_date=constraints_end_date,
        )

        return PlanningContext(
            planning_date=planning_date,
            athlete=athlete,
            primary_race=primary_race,
            training_races=training_races,
            readiness=readiness,
            recent_load=recent_load,
            recent_stats=recent_stats,
            constraints=constraints,
            constraints_end_date=constraints_end_date,
        )

    def active_constraints(
        self,
        athlete_profile_id: UUID,
        target_date: date | None = None,
    ) -> dict:
        """Retourne les contraintes applicables à une date précise."""
        effective_date = target_date or self.reference_date_provider()
        constraints = self.constraint_repository.list_overlapping(
            athlete_profile_id,
            effective_date,
            effective_date,
        )
        return {
            "status": "ok" if constraints else "empty",
            "target_date": effective_date.isoformat(),
            "constraint_count": len(constraints),
            "constraints": [
                {
                    "constraint_id": str(item.id),
                    "start_date": item.start_date.isoformat(),
                    "end_date": item.end_date.isoformat(),
                    "constraint_type": item.constraint_type,
                    "availability": item.availability,
                    "running_allowed": item.running_allowed,
                    "cross_training_allowed": item.cross_training_allowed,
                    "max_duration_minutes": item.max_duration_minutes,
                    "notes": item.notes[:500] if item.notes else None,
                }
                for item in constraints
            ],
            "interpretation_rules": [
                "Une contrainte est retournée si elle couvre la date demandée, bornes incluses.",
                "Ne pas extrapoler une contrainte avant son début ou après sa fin.",
                "Ne pas poser de diagnostic médical ni déduire une aptitude médicale.",
                "Si running_allowed est false, ne pas proposer de course à pied pour cette date.",
                "Si les données sont vides, cela signifie uniquement qu'aucune contrainte n'est enregistrée pour cette date.",
            ],
        }

    def weekly_plan_context(
        self,
        athlete_profile_id: UUID,
        week_start: date | None = None,
    ) -> dict:
        """Retourne le cadre hebdomadaire enregistré dans le domaine planning."""
        if self.weekly_plan_repository is None:
            raise RuntimeError("Le repository de plans hebdomadaires n'est pas configuré.")

        reference_date = self.reference_date_provider()
        effective_week_start = week_start or (
            reference_date - timedelta(days=reference_date.weekday())
        )
        plan = self.weekly_plan_repository.get_plan_for_week(
            athlete_profile_id,
            effective_week_start,
        )
        if plan is None:
            return {
                "status": "not_found",
                "week_start": effective_week_start.isoformat(),
                "message": (
                    "Aucun cadre hebdomadaire enregistré pour cette semaine. "
                    "Ne pas inventer la phase, le type de semaine ou les objectifs de charge."
                ),
            }

        return {
            "status": "ok",
            "week": {
                "start_date": plan.week_start.isoformat(),
                "end_date": plan.week_end.isoformat(),
                "phase": plan.phase,
                "week_type": plan.week_type,
                "phase_week_index": plan.phase_week_index,
                "generated_at": plan.generated_at.isoformat() if plan.generated_at else None,
                "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
            },
            "targets": {
                "load_target": plan.target_load,
                "load_min": plan.load_min,
                "load_max": plan.load_max,
                "reference_duration_minutes": plan.reference_duration_minutes,
                "target_duration_minutes": plan.target_duration_minutes,
                "long_endurance_reference_minutes": plan.long_endurance_reference_minutes,
            },
            "schedule": {
                "pressure": plan.schedule_pressure,
                "athlete_schedule_constrained": plan.athlete_schedule_constrained,
            },
        }

    def _get_training_races(
        self,
        *,
        athlete_profile_id: UUID,
        planning_date: date,
        primary_race: Race | None,
    ) -> tuple[Race, ...]:
        """Charge les courses préparatoires pertinentes."""

        if primary_race is None:
            return ()

        history_start_date = (
            planning_date
            - timedelta(days=7)
        )

        races = (
            self.race_repository
            .list_training_races_between(
                athlete_profile_id,
                history_start_date,
                primary_race.date,
            )
        )

        return tuple(
            race
            for race in races
            if race.date < primary_race.date
        )

    def _get_readiness(
        self,
        *,
        athlete_profile_id: UUID,
        planning_date: date,
    ) -> ReadinessAssessment | None:
        """Retourne le readiness lorsqu'il est disponible."""

        try:
            return self.readiness_service.calculate(
                athlete_profile_id,
                planning_date,
            )
        except ReadinessDataUnavailableError:
            return None

    def _get_recent_load(
        self,
        *,
        athlete_profile_id: UUID,
        planning_date: date,
        days: int,
    ) -> RecentTrainingLoad:
        """Calcule la charge récente avant la date de planification."""

        return self.recent_load_service.calculate(
            athlete_profile_id,
            planning_date,
            days=days,
        )

    def _get_recent_stats(
        self,
        *,
        athlete_profile_id: UUID,
        planning_date: date,
        days: int,
    ) -> TrainingStats:
        """Calcule les statistiques réelles précédant la planification."""

        start_date = (
            planning_date
            - timedelta(days=days)
        )

        end_date = (
            planning_date
            - timedelta(days=1)
        )

        return self.training_stats_service.calculate(
            athlete_profile_id,
            start_date,
            end_date,
        )

    def _get_constraints(
        self,
        *,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> tuple[AthleteConstraint, ...]:
        """Charge les contraintes temporaires de l'horizon demandé."""

        constraints = (
            self.constraint_repository.list_overlapping(
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return tuple(constraints)
