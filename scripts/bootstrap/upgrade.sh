#!/usr/bin/env bash

# OpenCoach - Mise à niveau d'une installation existante.
#
# Responsabilités :
# - vérifier l'état du dépôt ;
# - mettre éventuellement le dépôt Git à jour ;
# - valider les dépendances système ;
# - réinstaller les dépendances applicatives ;
# - reconstruire le frontend ;
# - appliquer automatiquement les migrations Alembic ;
# - redéployer les services et Nginx ;
# - redémarrer le backend ;
# - vérifier l'état final de l'application.
#
# Usage :
#   sudo ./scripts/bootstrap/upgrade.sh
#   sudo ./scripts/bootstrap/upgrade.sh --dev
#   sudo ./scripts/bootstrap/upgrade.sh --pull
#   sudo ./scripts/bootstrap/upgrade.sh --dev --pull

set -Eeuo pipefail


SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd -- "$SCRIPT_DIR/../.."
    pwd
)"

BOOTSTRAP_DIR="$PROJECT_ROOT/scripts/bootstrap"

# shellcheck source=../lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"


DEV_REQUESTED=0
PULL_REQUESTED=0

OPENCOACH_USER=""
OPENCOACH_GROUP=""

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
VENV_ALEMBIC="$PROJECT_ROOT/.venv/bin/alembic"


show_help() {
    printf '%s\n' \
        "OpenCoach - Mise à niveau"

    printf '\n'

    printf '%s\n' \
        "Utilisation :"

    printf '  %s\n' \
        "$0"

    printf '  %s --dev\n' \
        "$0"

    printf '  %s --pull\n' \
        "$0"

    printf '  %s --dev --pull\n' \
        "$0"

    printf '\n'

    printf '%s\n' \
        "--dev   Installe également les dépendances de développement."

    printf '%s\n' \
        "--pull  Met à jour la branche Git courante avant l'upgrade."
}


parse_arguments() {
    while (( $# > 0 )); do
        case "$1" in
            "--dev")
                DEV_REQUESTED=1
                ;;

            "--pull")
                PULL_REQUESTED=1
                ;;

            "--help"|"-h")
                show_help
                exit 0
                ;;

            *)
                log_error \
                    "Argument inconnu : $1"

                show_help >&2
                exit 2
                ;;
        esac

        shift
    done
}


require_root() {
    if (( EUID != 0 )); then
        log_error \
            "upgrade.sh doit être exécuté avec sudo."

        exit 1
    fi
}


resolve_project_owner() {
    OPENCOACH_USER="$(
        stat -c '%U' "$PROJECT_ROOT"
    )"

    OPENCOACH_GROUP="$(
        stat -c '%G' "$PROJECT_ROOT"
    )"

    if [[ "$OPENCOACH_USER" == "root" ]]; then
        log_error \
            "Le projet OpenCoach ne doit pas appartenir à root."

        return 1
    fi
}


run_as_project_owner() {
    runuser \
        -u "$OPENCOACH_USER" \
        -- \
        "$@"
}


validate_git_repository() {
    if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
        log_error \
            "Le projet OpenCoach n'est pas un dépôt Git."

        return 1
    fi

    if ! run_as_project_owner \
        git \
        -C "$PROJECT_ROOT" \
        diff \
        --quiet; then

        log_error \
            "Le dépôt contient des modifications non validées."

        log_error \
            "Committez ou annulez les modifications avant l'upgrade."

        return 1
    fi

    if ! run_as_project_owner \
        git \
        -C "$PROJECT_ROOT" \
        diff \
        --cached \
        --quiet; then

        log_error \
            "Le dépôt contient des modifications indexées non validées."

        return 1
    fi

    if [[ -n "$(
        run_as_project_owner \
            git \
            -C "$PROJECT_ROOT" \
            ls-files \
            --others \
            --exclude-standard
    )" ]]; then

        log_error \
            "Le dépôt contient des fichiers non suivis."

        log_error \
            "Nettoyez le dépôt avant l'upgrade."

        return 1
    fi

    log_success \
        "Dépôt Git propre."
}


update_repository() {
    if (( PULL_REQUESTED == 0 )); then
        log_info \
            "Mise à jour Git non demandée."

        return
    fi

    log_info \
        "Mise à jour du dépôt Git OpenCoach"

    run_as_project_owner \
        git \
        -C "$PROJECT_ROOT" \
        pull \
        --ff-only

    log_success \
        "Dépôt Git mis à jour."
}


validate_environment() {
    local arguments=(
        "--install"
    )

    if (( DEV_REQUESTED == 1 )); then
        arguments+=(
            "--dev"
        )
    fi

    log_info \
        "Validation et mise à niveau de l'environnement OpenCoach"

    "$BOOTSTRAP_DIR/check-environment.sh" \
        "${arguments[@]}"

    log_success \
        "Environnement OpenCoach valide."
}


show_database_revision_before() {
    if [[ ! -x "$VENV_ALEMBIC" ]]; then
        log_warning \
            "Alembic n'est pas encore disponible avant l'upgrade."

        return
    fi

    log_info \
        "Révision Alembic avant mise à niveau"

    (
        cd "$PROJECT_ROOT"

        run_as_project_owner \
            "$VENV_ALEMBIC" \
            current
    )
}


backup_sqlite_database() {
    local backup_result

    if [[ ! -x "$VENV_PYTHON" ]]; then
        log_error \
            "Python OpenCoach est introuvable avant la sauvegarde."

        return 1
    fi

    log_info \
        "Sauvegarde de la base SQLite avant migration"

    backup_result="$(
        run_as_project_owner \
            "$VENV_PYTHON" \
            - "$PROJECT_ROOT" <<'PYBACKUP'
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url


project_root = Path(
    sys.argv[1]
).resolve()

env_file = (
    project_root
    / ".env"
)

default_database = (
    project_root
    / "data"
    / "opencoach.db"
)

database_url = (
    f"sqlite:///{default_database}"
)


if env_file.is_file():
    for raw_line in env_file.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        if key.strip() != "OPENCOACH_DATABASE_URL":
            continue

        value = value.strip().strip(
            "\"'"
        )

        if value:
            database_url = value

        break


url = make_url(
    database_url
)

if url.get_backend_name() != "sqlite":
    print(
        "SKIPPED:not-sqlite"
    )
    raise SystemExit(0)


database = url.database

if (
    not database
    or database == ":memory:"
):
    print(
        "SKIPPED:no-file-database"
    )
    raise SystemExit(0)


database_path = Path(
    database
)

if not database_path.is_absolute():
    database_path = (
        project_root
        / database_path
    ).resolve()


if not database_path.exists():
    print(
        "SKIPPED:database-not-created"
    )
    raise SystemExit(0)


backup_dir = (
    project_root
    / "data"
    / "backups"
)

backup_dir.mkdir(
    parents=True,
    exist_ok=True,
)


timestamp = datetime.now().strftime(
    "%Y%m%d-%H%M%S"
)

backup_path = (
    backup_dir
    / (
        f"{database_path.stem}-"
        f"{timestamp}.db"
    )
)


with sqlite3.connect(
    database_path
) as source:
    with sqlite3.connect(
        backup_path
    ) as destination:
        source.backup(
            destination
        )

        integrity = destination.execute(
            "PRAGMA integrity_check"
        ).fetchone()


if (
    not integrity
    or integrity[0].lower() != "ok"
):
    backup_path.unlink(
        missing_ok=True
    )

    raise SystemExit(
        "La vérification d'intégrité de la sauvegarde a échoué."
    )


os.chmod(
    backup_path,
    0o600,
)

print(
    f"BACKUP:{backup_path}"
)
PYBACKUP
    )"

    case "$backup_result" in
        BACKUP:*)
            log_success \
                "Sauvegarde SQLite créée : ${backup_result#BACKUP:}"
            ;;

        SKIPPED:not-sqlite)
            log_info \
                "Base non SQLite : sauvegarde locale ignorée."
            ;;

        SKIPPED:no-file-database)
            log_info \
                "SQLite sans fichier persistant : sauvegarde ignorée."
            ;;

        SKIPPED:database-not-created)
            log_info \
                "Base SQLite absente : aucune sauvegarde nécessaire."
            ;;

        *)
            log_error \
                "Résultat inattendu pendant la sauvegarde SQLite."

            return 1
            ;;
    esac
}


upgrade_application() {
    local arguments=()

    if (( DEV_REQUESTED == 1 )); then
        arguments+=(
            "--dev"
        )
    fi

    log_info \
        "Mise à niveau de l'application OpenCoach"

    "$BOOTSTRAP_DIR/install-application.sh" \
        "${arguments[@]}"

    log_success \
        "Application OpenCoach mise à niveau."
}


redeploy_services() {
    log_info \
        "Redéploiement des services OpenCoach"

    "$BOOTSTRAP_DIR/install-services.sh"

    systemctl restart \
        opencoach-backend.service

    systemctl restart \
        opencoach-intervals-sync.timer

    log_success \
        "Services OpenCoach redémarrés."
}


verify_database_revision() {
    if [[ ! -x "$VENV_ALEMBIC" ]]; then
        log_error \
            "Alembic est introuvable après l'upgrade."

        return 1
    fi

    local current_revision
    local heads

    current_revision="$(
        cd "$PROJECT_ROOT"

        run_as_project_owner \
            "$VENV_ALEMBIC" \
            current \
            2>/dev/null \
            | awk '{ print $1 }'
    )"

    heads="$(
        cd "$PROJECT_ROOT"

        run_as_project_owner \
            "$VENV_ALEMBIC" \
            heads \
            2>/dev/null \
            | awk '{ print $1 }'
    )"

    if [[ -z "$current_revision" ]]; then
        log_error \
            "Impossible de déterminer la révision Alembic courante."

        return 1
    fi

    if [[ "$current_revision" != "$heads" ]]; then
        log_error \
            "La base n'est pas à la révision Alembic attendue."

        log_error \
            "Courante : $current_revision ; attendue : $heads"

        return 1
    fi

    log_success \
        "Base de données à la dernière révision Alembic : $current_revision"
}


verify_services() {
    local failed=0

    for service in \
        opencoach-backend.service \
        nginx.service \
        opencoach-intervals-sync.timer
    do
        if systemctl is-active \
            --quiet \
            "$service"; then

            log_success \
                "$service actif"

        else
            log_error \
                "$service inactif"

            failed=1
        fi
    done

    return "$failed"
}


verify_http() {
    if [[ ! -x "$VENV_PYTHON" ]]; then
        log_error \
            "Python OpenCoach introuvable."

        return 1
    fi

    log_info \
        "Vérification HTTP d'OpenCoach"

    if ! "$VENV_PYTHON" - <<'PYHTTP'
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def check(
    url: str,
    *,
    attempts: int = 10,
    delay_seconds: float = 1.0,
) -> None:
    import time

    last_error: str | None = None

    for attempt in range(
        1,
        attempts + 1,
    ):
        try:
            with urlopen(
                url,
                timeout=10,
            ) as response:
                status = response.status

            if status == 200:
                print(
                    f"[HTTP 200] {url}"
                )
                return

            last_error = (
                f"HTTP {status}"
            )

        except HTTPError as exc:
            last_error = (
                f"HTTP {exc.code}"
            )

        except URLError as exc:
            last_error = (
                f"indisponible : "
                f"{exc.reason}"
            )

        if attempt < attempts:
            print(
                (
                    f"[HTTP RETRY "
                    f"{attempt}/{attempts}] "
                    f"{url} -> {last_error}"
                )
            )

            time.sleep(
                delay_seconds
            )

    raise SystemExit(
        (
            f"{url} -> échec après "
            f"{attempts} tentative(s) : "
            f"{last_error}"
        )
    )


check(
    "http://127.0.0.1/"
)

check(
    "http://127.0.0.1/api/health/ready"
)
PYHTTP
    then
        log_error \
            "La vérification HTTP OpenCoach a échoué."

        return 1
    fi

    log_success \
        "OpenCoach répond correctement via Nginx."
}


get_server_ipv4() {
    local server_ip=""

    if command -v ip >/dev/null 2>&1; then
        server_ip="$(
            ip route get 1.1.1.1 2>/dev/null \
                | awk '
                    {
                        for (i = 1; i <= NF; i++) {
                            if ($i == "src" && (i + 1) <= NF) {
                                print $(i + 1)
                                exit
                            }
                        }
                    }
                '
        )"
    fi

    if [[ -z "$server_ip" ]] \
        && command -v hostname >/dev/null 2>&1; then

        server_ip="$(
            hostname -I 2>/dev/null \
                | awk '{ print $1 }'
        )"
    fi

    printf '%s' \
        "$server_ip"
}


show_access_information() {
    local server_ip

    server_ip="$(
        get_server_ipv4
    )"

    if [[ -n "$server_ip" ]]; then
        log_info \
            "OpenCoach est accessible sur : http://$server_ip"
    else
        log_warning \
            "Impossible de déterminer l'adresse IP du serveur."
    fi
}


main() {
    parse_arguments "$@"

    require_root
    resolve_project_owner

    log_info \
        "Mise à niveau OpenCoach"

    validate_git_repository

    update_repository

    show_database_revision_before

    validate_environment

    backup_sqlite_database

    upgrade_application

    redeploy_services

    verify_database_revision

    verify_services

    verify_http

    show_access_information

    log_success \
        "Mise à niveau OpenCoach terminée avec succès."
}


main "$@"
