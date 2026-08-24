#!/usr/bin/env bash

# OpenCoach - Installation des services systemd.
#
# Responsabilités :
# - identifier l'utilisateur propriétaire du projet ;
# - préparer et sécuriser .env ;
# - appliquer les permissions ;
# - installer les unités systemd ;
# - activer le backend au démarrage ;
# - activer le timer de synchronisation Intervals.

set -Eeuo pipefail


SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd -- "$SCRIPT_DIR/../.."
    pwd
)"

SYSTEMD_SOURCE_DIR="$PROJECT_ROOT/systemd"
SYSTEMD_TARGET_DIR="/etc/systemd/system"

ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"


if (( EUID != 0 )); then
    printf '%s\n' \
        "ERREUR : install-services.sh doit être exécuté avec sudo." \
        >&2

    exit 1
fi


OPENCOACH_USER="$(
    stat -c '%U' "$PROJECT_ROOT"
)"

OPENCOACH_GROUP="$(
    stat -c '%G' "$PROJECT_ROOT"
)"


if [[ "$OPENCOACH_USER" == "root" ]]; then
    printf '%s\n' \
        "ERREUR : le projet OpenCoach ne doit pas appartenir à root." \
        >&2

    exit 1
fi


if [[ ! -x "$VENV_PYTHON" ]]; then
    printf '%s\n' \
        "ERREUR : environnement virtuel OpenCoach introuvable :" \
        >&2

    printf '  %s\n' \
        "$VENV_PYTHON" \
        >&2

    exit 1
fi


prepare_environment_file() {
    local generated_key

    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ ! -f "$ENV_EXAMPLE" ]]; then
            printf '%s\n' \
                "ERREUR : .env et .env.example sont absents." \
                >&2

            return 1
        fi

        printf '%s\n' \
            "[INFO] Création du fichier .env"

        cp \
            "$ENV_EXAMPLE" \
            "$ENV_FILE"

        generated_key="$(
            "$VENV_PYTHON" -c \
                'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
        )"

        sed -i \
            "s|^OPENCOACH_SECRET_KEY=.*$|OPENCOACH_SECRET_KEY=$generated_key|" \
            "$ENV_FILE"

        printf '%s\n' \
            "[OK] Nouvelle OPENCOACH_SECRET_KEY générée."
    fi


    if ! grep -Eq \
        '^[[:space:]]*OPENCOACH_SECRET_KEY=.+$' \
        "$ENV_FILE"; then

        printf '%s\n' \
            "ERREUR : OPENCOACH_SECRET_KEY est absente ou vide dans .env." \
            >&2

        printf '%s\n' \
            "Si une base OpenCoach existante est restaurée, restaurez également sa clé d'origine." \
            >&2

        return 1
    fi


    chown \
        "$OPENCOACH_USER:$OPENCOACH_GROUP" \
        "$ENV_FILE"

    chmod 600 \
        "$ENV_FILE"
}


apply_project_permissions() {
    printf '%s\n' \
        "[INFO] Application des permissions OpenCoach"


    # Bibliothèques shell : sourcées, jamais exécutées directement.
    if [[ -d "$PROJECT_ROOT/scripts/lib" ]]; then
        find "$PROJECT_ROOT/scripts/lib" \
            -type f \
            -name '*.sh' \
            -exec chmod 644 {} +
    fi


    # Points d'entrée exécutables.
    for directory in \
        "$PROJECT_ROOT/scripts/bootstrap" \
        "$PROJECT_ROOT/scripts/dev" \
        "$PROJECT_ROOT/scripts/maintenance"
    do
        if [[ -d "$directory" ]]; then
            find "$directory" \
                -type f \
                -name '*.sh' \
                -exec chmod 755 {} +
        fi
    done


    # Scripts éventuels directement sous scripts/.
    find "$PROJECT_ROOT/scripts" \
        -maxdepth 1 \
        -type f \
        -name '*.sh' \
        -exec chmod 755 {} +


    if [[ -d "$SYSTEMD_SOURCE_DIR" ]]; then
        find "$SYSTEMD_SOURCE_DIR" \
            -type f \
            \( -name '*.service' -o -name '*.timer' \) \
            -exec chmod 644 {} +
    fi
}


escape_sed_replacement() {
    printf '%s' "$1" \
        | sed \
            -e 's/[&|]/\\&/g'
}


render_unit() {
    local source_file="$1"
    local target_file="$2"

    local escaped_root
    local escaped_user
    local escaped_group

    if [[ ! -f "$source_file" ]]; then
        printf '%s\n' \
            "ERREUR : unité systemd source introuvable : $source_file" \
            >&2

        return 1
    fi

    escaped_root="$(
        escape_sed_replacement \
            "$PROJECT_ROOT"
    )"

    escaped_user="$(
        escape_sed_replacement \
            "$OPENCOACH_USER"
    )"

    escaped_group="$(
        escape_sed_replacement \
            "$OPENCOACH_GROUP"
    )"

    sed \
        -e "s|@PROJECT_ROOT@|$escaped_root|g" \
        -e "s|@OPENCOACH_USER@|$escaped_user|g" \
        -e "s|@OPENCOACH_GROUP@|$escaped_group|g" \
        "$source_file" \
        > "$target_file"

    chmod 644 \
        "$target_file"
}


install_systemd_units() {
    printf '%s\n' \
        "[INFO] Installation des unités systemd"

    render_unit \
        "$SYSTEMD_SOURCE_DIR/opencoach-backend.service" \
        "$SYSTEMD_TARGET_DIR/opencoach-backend.service"

    render_unit \
        "$SYSTEMD_SOURCE_DIR/opencoach-intervals-sync.service" \
        "$SYSTEMD_TARGET_DIR/opencoach-intervals-sync.service"

    render_unit \
        "$SYSTEMD_SOURCE_DIR/opencoach-intervals-sync.timer" \
        "$SYSTEMD_TARGET_DIR/opencoach-intervals-sync.timer"

    systemctl daemon-reload
}


enable_services() {
    # Activation du backend pour les démarrages futurs.
    # Il n'est pas démarré immédiatement pour éviter un conflit
    # avec un serveur de développement déjà présent sur le port 8000.
    systemctl enable \
        opencoach-backend.service

    # Le timer Intervals peut être démarré immédiatement.
    systemctl enable --now \
        opencoach-intervals-sync.timer
}


main() {
    prepare_environment_file

    apply_project_permissions

    install_systemd_units

    enable_services

    printf '%s\n' \
        "[OK] Services OpenCoach installés."

    printf '%s\n' \
        "[INFO] Backend activé pour le prochain démarrage."

    printf '%s\n' \
        "[INFO] Synchronisation Intervals active toutes les 15 minutes."
}


main "$@"
