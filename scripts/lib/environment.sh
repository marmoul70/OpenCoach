#!/usr/bin/env bash

# OpenCoach - Gestion de l'environnement applicatif.
#
# Charge les variables du fichier .env du projet et valide
# les variables indispensables au fonctionnement du backend.

set -Eeuo pipefail


load_opencoach_environment() {
    local project_root="$1"
    local env_file="$project_root/.env"

    if [[ ! -f "$env_file" ]]; then
        printf '%s\n'             "ERREUR : fichier d'environnement introuvable : $env_file"             >&2

        return 1
    fi

    set -a

    # shellcheck disable=SC1090
    source "$env_file"

    set +a
}


validate_opencoach_environment() {
    local missing=0

    if [[ -z "${OPENCOACH_SECRET_KEY:-}" ]]; then
        printf '%s\n'             "ERREUR : OPENCOACH_SECRET_KEY n'est pas configurée."             >&2

        missing=1
    fi

    if (( missing > 0 )); then
        return 1
    fi
}


load_and_validate_opencoach_environment() {
    local project_root="$1"

    load_opencoach_environment         "$project_root"

    validate_opencoach_environment
}
