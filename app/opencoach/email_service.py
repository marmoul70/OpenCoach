"""Envoi des e-mails transactionnels OpenCoach."""

from __future__ import annotations

import logging
import os
import smtplib

from email.message import EmailMessage


logger = logging.getLogger(__name__)


def _required_env(
    name: str,
) -> str:
    value = os.getenv(
        name,
        "",
    ).strip()

    if not value:
        raise RuntimeError(
            f"Variable SMTP absente : {name}"
        )

    return value


def send_welcome_email(
    *,
    recipient_email: str,
    first_name: str,
    username: str,
) -> None:
    """Envoie l'identifiant OpenCoach après création du compte.

    Le code PIN n'est volontairement jamais transmis par e-mail.
    """

    smtp_host = _required_env(
        "SMTP_HOST"
    )
    smtp_port = int(
        _required_env(
            "SMTP_PORT"
        )
    )
    smtp_username = _required_env(
        "SMTP_USERNAME"
    )
    smtp_password = _required_env(
        "SMTP_PASSWORD"
    )
    from_email = _required_env(
        "SMTP_FROM_EMAIL"
    )
    from_name = (
        os.getenv(
            "SMTP_FROM_NAME",
            "OpenCoach",
        ).strip()
        or "OpenCoach"
    )

    message = EmailMessage()
    message["Subject"] = (
        "Bienvenue sur OpenCoach"
    )
    message["From"] = (
        f"{from_name} <{from_email}>"
    )
    message["To"] = recipient_email

    display_name = (
        first_name.strip()
        or "athlète"
    )

    message.set_content(
        f"Bonjour {display_name},\n\n"
        "Votre compte OpenCoach a bien été créé.\n\n"
        "Votre identifiant de connexion est :\n\n"
        f"{username}\n\n"
        "Conservez cet identifiant.\n"
        "Votre code PIN reste celui que vous avez choisi "
        "lors de votre inscription.\n\n"
        "OpenCoach\n"
    )

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=20,
    ) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(
            smtp_username,
            smtp_password,
        )
        smtp.send_message(
            message
        )


def send_welcome_email_safely(
    *,
    recipient_email: str,
    first_name: str,
    username: str,
) -> bool:
    """Envoie le mail sans invalider un compte déjà créé."""

    try:
        send_welcome_email(
            recipient_email=recipient_email,
            first_name=first_name,
            username=username,
        )

    except Exception:
        logger.exception(
            (
                "Impossible d'envoyer l'e-mail "
                "de bienvenue OpenCoach à %s."
            ),
            recipient_email,
        )
        return False

    return True
