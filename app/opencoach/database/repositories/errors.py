class ProfileRepositoryError(RuntimeError):
    """Erreur de persistance du profil athlète."""

class ActivityRepositoryError(RuntimeError):
    """Erreur de persistance d'une activité sportive."""

class WellnessRepositoryError(RuntimeError):
    """Erreur de persistance des données Wellness."""

class IntegrationConnectionRepositoryError(RuntimeError):
    """Erreur de persistance des connexions externes."""

class TrainingSessionRepositoryError(RuntimeError):
    """Erreur de persistance des séances d'entraînement."""

class DailyContextRepositoryError(RuntimeError):
    """Erreur de persistance du contexte quotidien."""

class RaceRepositoryError(RuntimeError):
    """Erreur de persistance des courses."""