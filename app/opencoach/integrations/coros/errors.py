class CorosMcpError(RuntimeError):
    """Erreur générique du connecteur COROS MCP."""


class CorosMcpAuthenticationError(CorosMcpError):
    """Jeton COROS absent, expiré ou refusé."""


class CorosMcpProtocolError(CorosMcpError):
    """Réponse MCP invalide ou incompatible."""
