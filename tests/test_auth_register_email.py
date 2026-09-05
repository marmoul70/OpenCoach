"""Tests de l'e-mail envoyé lors de l'inscription."""

from __future__ import annotations

from opencoach.api import auth


class FakeDatabase:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.added = []

    def scalar(
        self,
        statement,
    ):
        # Aucun utilisateur existant avec cet e-mail.
        return None

    def add(
        self,
        value,
    ):
        self.added.append(
            value
        )

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_register_keeps_account_when_welcome_email_fails(
    monkeypatch,
):
    database = FakeDatabase()

    mail_call = {}

    monkeypatch.setattr(
        auth,
        "SessionLocal",
        lambda: database,
    )

    monkeypatch.setattr(
        auth,
        "generate_username",
        lambda *args, **kwargs: "mar123",
    )

    monkeypatch.setattr(
        auth,
        "hash_pin",
        lambda pin: (
            "hashed-pin",
            "pin-salt",
        ),
    )

    def fake_welcome_email(
        *,
        recipient_email,
        first_name,
        username,
    ):
        mail_call.update(
            {
                "recipient_email": recipient_email,
                "first_name": first_name,
                "username": username,
            }
        )

        # Simulation d'un échec SMTP déjà absorbé
        # par send_welcome_email_safely().
        return False

    monkeypatch.setattr(
        auth,
        "send_welcome_email_safely",
        fake_welcome_email,
    )

    payload = auth.RegisterRequest(
        first_name="Sébastien",
        last_name="Martin",
        email="SEBASTIEN@example.com",
        pin="123456",
    )

    response = auth.register(
        payload
    )

    assert response.username == "mar123"

    assert (
        response.email
        == "sebastien@example.com"
    )

    assert database.committed is True
    assert database.rolled_back is False
    assert database.closed is True

    assert mail_call == {
        "recipient_email": "sebastien@example.com",
        "first_name": "Sébastien",
        "username": "mar123",
    }


def test_register_route_declares_http_201():
    register_route = next(
        route
        for route in auth.router.routes
        if (
            route.path
            == "/api/auth/register"
        )
    )

    assert (
        register_route.status_code
        == 201
    )
