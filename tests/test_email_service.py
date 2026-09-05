"""Tests du service e-mail transactionnel OpenCoach."""

from __future__ import annotations

import smtplib

import pytest

from opencoach.email_service import (
    send_welcome_email,
    send_welcome_email_safely,
)


class FakeSMTP:
    last_instance = None

    def __init__(
        self,
        host,
        port,
        timeout,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.logged_in = None
        self.message = None
        self.started_tls = False

        FakeSMTP.last_instance = self

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    def ehlo(self):
        return None

    def starttls(self):
        self.started_tls = True

    def login(
        self,
        username,
        password,
    ):
        self.logged_in = (
            username,
            password,
        )

    def send_message(
        self,
        message,
    ):
        self.message = message


@pytest.fixture
def smtp_environment(
    monkeypatch: pytest.MonkeyPatch,
):
    values = {
        "SMTP_HOST": "smtp.example.test",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "smtp-user",
        "SMTP_PASSWORD": "smtp-password",
        "SMTP_FROM_EMAIL": "noreply@example.test",
        "SMTP_FROM_NAME": "OpenCoach",
    }

    for key, value in values.items():
        monkeypatch.setenv(
            key,
            value,
        )


def test_welcome_email_contains_username_but_not_pin(
    monkeypatch: pytest.MonkeyPatch,
    smtp_environment,
):
    monkeypatch.setattr(
        smtplib,
        "SMTP",
        FakeSMTP,
    )

    send_welcome_email(
        recipient_email="athlete@example.test",
        first_name="Sébastien",
        username="mar123",
    )

    smtp = FakeSMTP.last_instance

    assert smtp is not None
    assert smtp.host == "smtp.example.test"
    assert smtp.port == 587
    assert smtp.started_tls is True
    assert smtp.logged_in == (
        "smtp-user",
        "smtp-password",
    )

    message = smtp.message

    assert message is not None
    assert (
        message["To"]
        == "athlete@example.test"
    )
    assert (
        message["From"]
        == "OpenCoach <noreply@example.test>"
    )

    body = message.get_content()

    assert "mar123" in body
    assert "Sébastien" in body
    assert "code PIN" in body

    # Un PIN ne doit jamais être injecté
    # dans ce service.
    assert "123456" not in body


def test_safe_welcome_email_does_not_propagate_smtp_failure(
    monkeypatch: pytest.MonkeyPatch,
    smtp_environment,
):
    class FailingSMTP(FakeSMTP):
        def login(
            self,
            username,
            password,
        ):
            raise smtplib.SMTPAuthenticationError(
                535,
                b"Authentication failed",
            )

    monkeypatch.setattr(
        smtplib,
        "SMTP",
        FailingSMTP,
    )

    result = send_welcome_email_safely(
        recipient_email="athlete@example.test",
        first_name="Sébastien",
        username="mar123",
    )

    assert result is False


def test_missing_smtp_configuration_is_absorbed(
    monkeypatch: pytest.MonkeyPatch,
):
    for key in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "SMTP_FROM_NAME",
    ):
        monkeypatch.delenv(
            key,
            raising=False,
        )

    result = send_welcome_email_safely(
        recipient_email="athlete@example.test",
        first_name="Sébastien",
        username="mar123",
    )

    assert result is False
