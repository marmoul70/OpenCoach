class IntervalsError(RuntimeError):
    """Erreur générique de l'intégration Intervals.icu."""


class IntervalsAuthenticationError(IntervalsError):
    """Échec d'authentification auprès d'Intervals.icu."""


class IntervalsApiError(IntervalsError):
    """Erreur retournée par l'API Intervals.icu."""

class IntervalsDataError(IntervalsError):
    """Données Intervals.icu absentes ou invalides."""