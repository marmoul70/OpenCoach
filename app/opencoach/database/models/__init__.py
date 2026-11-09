from opencoach.database.models.activity import Activity
from .activity_equipment_assignment import ActivityEquipmentAssignment
from .activity_detail import ActivityDetail, ActivityInterval, ActivityStream
from opencoach.database.models.athlete_profile import AthleteProfile
from opencoach.database.models.bike import Bike
from opencoach.database.models.shoe import Shoe
from opencoach.database.models.user import User
from opencoach.database.models.watch import Watch
from opencoach.database.models.wellness import WellnessDaily
from opencoach.database.models.coros_daily_data import CorosDailyData
from opencoach.database.models.coros_sync_lock import CorosSyncLock
from opencoach.database.models.integration_connection import IntegrationConnection
from opencoach.database.models.training_session import TrainingSession
from opencoach.database.models.weekly_training_plan import WeeklyTrainingPlan
from opencoach.database.models.daily_context import DailyContext
from opencoach.database.models.race import Race
from .athlete_constraint import AthleteConstraint
from .physiological_measurement import PhysiologicalMeasurement
from .notification import Notification
from .ai_coach_preference import AICoachPreference

__all__ = [
    "Activity",
    "ActivityEquipmentAssignment",
    "ActivityDetail",
    "ActivityInterval",
    "ActivityStream",
    "AthleteProfile",
    "Bike",
    "Shoe",
    "User",
    "Watch",
    "WellnessDaily",
    "IntegrationConnection",
    "CorosDailyData",
    "CorosSyncLock",
    "TrainingSession",
    "WeeklyTrainingPlan",
    "DailyContext",
    "Race",
    "AthleteConstraint",
    "PhysiologicalMeasurement",
    "Notification",
    "AICoachPreference",
]

from .daily_checkin import DailyCheckIn
from .daily_adaptation import DailyAdaptationProposal
from .physiological_test_proposal import PhysiologicalTestProposal
from .session_execution_analysis import SessionExecutionAnalysis
from .push_subscription import PushSubscription
from .weekly_debrief import WeeklyDebriefRecord
