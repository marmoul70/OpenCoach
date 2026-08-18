import os

from cryptography.fernet import Fernet, InvalidToken


class SecretCipherError(RuntimeError):
    """Erreur lors du chiffrement ou déchiffrement d'un secret."""


class SecretCipher:
    """Chiffre et déchiffre les secrets OpenCoach avec Fernet."""

    ENV_KEY = "OPENCOACH_SECRET_KEY"

    def __init__(
        self,
        key: str | bytes,
    ) -> None:
        try:
            encoded_key = (
                key.encode()
                if isinstance(key, str)
                else key
            )

            self._fernet = Fernet(
                encoded_key,
            )

        except (TypeError, ValueError) as exc:
            raise SecretCipherError(
                "Clé de chiffrement OpenCoach invalide."
            ) from exc

    @classmethod
    def from_env(cls) -> "SecretCipher":
        key = os.getenv(
            cls.ENV_KEY,
            "",
        ).strip()

        if not key:
            raise SecretCipherError(
                "OPENCOACH_SECRET_KEY n'est pas configurée."
            )

        return cls(key)

    def encrypt(
        self,
        value: str,
    ) -> bytes:
        if not value:
            raise SecretCipherError(
                "Le secret à chiffrer est vide."
            )

        return self._fernet.encrypt(
            value.encode(),
        )

    def decrypt(
        self,
        value: bytes,
    ) -> str:
        try:
            decrypted = self._fernet.decrypt(
                value,
            )

        except InvalidToken as exc:
            raise SecretCipherError(
                "Impossible de déchiffrer le secret."
            ) from exc

        return decrypted.decode()
