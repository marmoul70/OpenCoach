class ProfileRepositoryError(RuntimeError):
    """Erreur de persistance du profil athlète."""

class ActivityRepositoryError(RuntimeError):
    """Erreur de persistance d'une activité sportive."""

class WellnessRepositoryError(RuntimeError):
    """Erreur de persistance des données Wellness."""