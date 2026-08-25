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

# shellcheck source=../lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

SYSTEMD_SOURCE_DIR="$PROJECT_ROOT/systemd"
SYSTEMD_TARGET_DIR="/etc/systemd/system"

NGINX_SOURCE_FILE="$PROJECT_ROOT/nginx/opencoach.conf"
NGINX_TARGET_FILE="/etc/nginx/sites-available/opencoach"
NGINX_ENABLED_FILE="/etc/nginx/sites-enabled/opencoach"
NGINX_FRONTEND_DIR="/var/www/opencoach"

ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"


if (( EUID != 0 )); then
    log_error \
        "install-services.sh doit être exécuté avec sudo."

    exit 1
fi


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


if [[ ! -x "$VENV_PYTHON" ]]; then
    log_error \
        "Environnement virtuel OpenCoach introuvable : $VENV_PYTHON"

    exit 1
fi


prepare_environment_file() {
    local generated_key

    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ ! -f "$ENV_EXAMPLE" ]]; then
            log_error \
                ".env et .env.example sont absents."

            return 1
        fi

        log_info \
            "Création du fichier .env"

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

        log_success \
            "Nouvelle OPENCOACH_SECRET_KEY générée."
    fi


    if ! grep -Eq \
        '^[[:space:]]*OPENCOACH_SECRET_KEY=.+$' \
        "$ENV_FILE"; then

        log_error \
            "OPENCOACH_SECRET_KEY est absente ou vide dans .env."

        log_error \
            "Si une base OpenCoach existante est restaurée, restaurez également sa clé d'origine."

        return 1
    fi


    chown \
        "$OPENCOACH_USER:$OPENCOACH_GROUP" \
        "$ENV_FILE"

    chmod 600 \
        "$ENV_FILE"
}


apply_project_permissions() {
    log_info \
        "Application des permissions OpenCoach"


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
        log_error \
            "Unité systemd source introuvable : $source_file"

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
    log_info \
        "Installation des unités systemd"

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


install_nginx_configuration() {
    if [[ ! -f "$NGINX_SOURCE_FILE" ]]; then
        log_error \
            "Configuration Nginx source introuvable : $NGINX_SOURCE_FILE"

        return 1
    fi

    if [[ ! -f "$PROJECT_ROOT/frontend/dist/index.html" ]]; then
        log_error \
            "Frontend compilé introuvable : frontend/dist/index.html"

        return 1
    fi

    log_info \
        "Déploiement du frontend OpenCoach"

    install \
        -d \
        -o root \
        -g root \
        -m 755 \
        "$NGINX_FRONTEND_DIR"

    rm -rf \
        "$NGINX_FRONTEND_DIR"/*

    cp -a \
        "$PROJECT_ROOT/frontend/dist/." \
        "$NGINX_FRONTEND_DIR/"

    find "$NGINX_FRONTEND_DIR" \
        -type d \
        -exec chmod 755 {} +

    find "$NGINX_FRONTEND_DIR" \
        -type f \
        -exec chmod 644 {} +

    log_info \
        "Installation de la configuration Nginx OpenCoach"

    cp \
        "$NGINX_SOURCE_FILE" \
        "$NGINX_TARGET_FILE"

    ln -sfn \
        "$NGINX_TARGET_FILE" \
        "$NGINX_ENABLED_FILE"

    rm -f \
        /etc/nginx/sites-enabled/default

    if ! nginx -t; then
        log_error \
            "La configuration Nginx OpenCoach est invalide."

        return 1
    fi

    systemctl enable nginx
    systemctl restart nginx

    log_success \
        "Nginx OpenCoach installé et démarré."
}

enable_services() {
    # Le backend de production écoute uniquement sur localhost.
    # Il peut donc être activé et démarré immédiatement.
    systemctl enable --now \
        opencoach-backend.service

    # Le timer Intervals peut être démarré immédiatement.
    systemctl enable --now \
        opencoach-intervals-sync.timer
}


main() {
    prepare_environment_file

    apply_project_permissions

    install_systemd_units

    install_nginx_configuration

    enable_services

    log_success \
        "Services OpenCoach installés."

    log_info \
        "Backend activé pour le prochain démarrage."

    log_info \
        "Synchronisation Intervals active toutes les 15 minutes."
}


main "$@"
