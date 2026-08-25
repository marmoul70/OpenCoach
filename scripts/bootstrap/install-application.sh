#!/usr/bin/env bash

# OpenCoach - Installation de l'application.
#
# Responsabilités :
# - créer l'environnement virtuel Python ;
# - installer les dépendances Python ;
# - installer les dépendances frontend ;
# - appliquer les migrations Alembic.
#
# Usage :
#   sudo ./scripts/bootstrap/install-application.sh
#   sudo ./scripts/bootstrap/install-application.sh --dev

set -Eeuo pipefail


SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd -- "$SCRIPT_DIR/../.."
    pwd
)"

# shellcheck source=../lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_ALEMBIC="$VENV_DIR/bin/alembic"

FRONTEND_DIR="$PROJECT_ROOT/frontend"

DEV_REQUESTED=0


show_help() {
    printf '%s\n' "OpenCoach - Installation applicative"
    printf '\n'
    printf '%s\n' "Utilisation :"
    printf '  %s\n' "$0"
    printf '  %s --dev\n' "$0"
    printf '  %s --help\n' "$0"
}


parse_arguments() {
    while (( $# > 0 )); do
        case "$1" in
            "--dev")
                DEV_REQUESTED=1
                ;;

            "--help"|"-h")
                show_help
                exit 0
                ;;

            *)
                printf 'ERREUR : argument inconnu : %s\n' "$1" >&2
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
            "install-application.sh doit être exécuté avec sudo."

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

        exit 1
    fi
}


run_as_project_owner() {
    runuser \
        -u "$OPENCOACH_USER" \
        -- \
        "$@"
}


create_virtual_environment() {
    if [[ -x "$VENV_PYTHON" ]]; then
        log_success \
            "Environnement virtuel Python déjà présent."

        return
    fi

    log_info \
        "Création de l'environnement virtuel Python"

    run_as_project_owner \
        python3 \
        -m venv \
        "$VENV_DIR"

    if [[ ! -x "$VENV_PYTHON" ]]; then
        log_error \
            "Création de l'environnement virtuel impossible."

        return 1
    fi

    log_success \
        "Environnement virtuel Python créé."
}


install_python_application() {
    local install_target="."

    if (( DEV_REQUESTED == 1 )); then
        install_target=".[dev]"
    fi

    log_info \
        "Mise à jour de pip"

    run_as_project_owner \
        "$VENV_PYTHON" \
        -m pip \
        install \
        --upgrade \
        pip

    log_info \
        "Installation d'OpenCoach : $install_target"

    (
        cd "$PROJECT_ROOT"

        run_as_project_owner \
            "$VENV_PYTHON" \
            -m pip \
            install \
            -e \
            "$install_target"
    )

    log_success \
        "Dépendances Python installées."
}


install_frontend_application() {
    if [[ ! -f "$FRONTEND_DIR/package-lock.json" ]]; then
        log_error \
            "frontend/package-lock.json est introuvable."

        return 1
    fi

    log_info \
        "Installation des dépendances frontend"

    (
        cd "$FRONTEND_DIR"

        run_as_project_owner \
            npm ci
    )

    log_success \
        "Dépendances frontend installées."
}


apply_database_migrations() {
    if [[ ! -x "$VENV_ALEMBIC" ]]; then
        log_error \
            "Alembic est introuvable dans l'environnement virtuel."

        return 1
    fi

    log_info \
        "Application des migrations Alembic"

    (
        cd "$PROJECT_ROOT"

        run_as_project_owner \
            "$VENV_ALEMBIC" \
            upgrade \
            head
    )

    log_success \
        "Base de données à jour."
}


main() {
    parse_arguments "$@"

    require_root
    resolve_project_owner

    log_info \
        "Installation applicative OpenCoach"

    create_virtual_environment

    install_python_application

    install_frontend_application

    apply_database_migrations

    log_success \
        "Installation applicative OpenCoach terminée."
}


main "$@"
