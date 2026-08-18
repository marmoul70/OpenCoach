from cryptography.fernet import Fernet
import pytest

from opencoach.security import (
    SecretCipher,
    SecretCipherError,
)


def test_secret_cipher_encrypts_and_decrypts() -> None:
    key = Fernet.generate_key()

    cipher = SecretCipher(key)

    encrypted = cipher.encrypt(
        "secret-api-key"
    )

    assert encrypted != b"secret-api-key"

    assert cipher.decrypt(
        encrypted
    ) == "secret-api-key"


def test_secret_cipher_rejects_empty_secret() -> None:
    cipher = SecretCipher(
        Fernet.generate_key()
    )

    with pytest.raises(
        SecretCipherError,
        match="secret à chiffrer est vide",
    ):
        cipher.encrypt("")


def test_secret_cipher_rejects_invalid_key() -> None:
    with pytest.raises(
        SecretCipherError,
        match="Clé de chiffrement OpenCoach invalide",
    ):
        SecretCipher(
            "invalid-key"
        )


def test_secret_cipher_rejects_invalid_token() -> None:
    cipher = SecretCipher(
        Fernet.generate_key()
    )

    with pytest.raises(
        SecretCipherError,
        match="Impossible de déchiffrer",
    ):
        cipher.decrypt(
            b"invalid-token"
        )
