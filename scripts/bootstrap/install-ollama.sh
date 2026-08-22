#!/usr/bin/env bash

# OpenCoach - Installation d'Ollama
#
# Installe et vérifie le moteur IA local Ollama.
# Ce script est conçu pour être idempotent.

set -Eeuo pipefail


SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd -- "$SCRIPT_DIR/../.."
    pwd
)"

# shellcheck source=scripts/lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

# shellcheck source=scripts/lib/system.sh
source "$PROJECT_ROOT/scripts/lib/system.sh"


OLLAMA_INSTALL_URL="${OLLAMA_INSTALL_URL:-https://ollama.com/install.sh}"
OLLAMA_VERSION="${OLLAMA_VERSION:-}"


require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        log_error \
            "L'installation d'Ollama doit être exécutée avec les privilèges root."

        return 1
    fi
}


is_ollama_installed() {
    command -v ollama >/dev/null 2>&1
}


install_ollama() {
    if is_ollama_installed; then
        log_success \
            "Ollama est déjà installé."

        return 0
    fi

    log_info \
        "Installation d'Ollama."

    require_command curl

    if [[ -n "$OLLAMA_VERSION" ]]; then
        log_info \
            "Version Ollama demandée : $OLLAMA_VERSION"

        curl -fsSL "$OLLAMA_INSTALL_URL" \
            | OLLAMA_VERSION="$OLLAMA_VERSION" sh
    else
        curl -fsSL "$OLLAMA_INSTALL_URL" \
            | sh
    fi

    if ! is_ollama_installed; then
        log_error \
            "Ollama n'est pas disponible après l'installation."

        return 1
    fi

    log_success \
        "Ollama installé."
}


enable_ollama_service() {
    require_command systemctl

    log_info \
        "Activation du service Ollama."

    systemctl daemon-reload
    systemctl enable ollama
    systemctl start ollama

    log_success \
        "Service Ollama activé."
}


check_ollama_service() {
    if ! systemctl is-active \
        --quiet \
        ollama
    then
        log_error \
            "Le service Ollama n'est pas actif."

        return 1
    fi

    log_success \
        "Service Ollama actif."
}


show_ollama_version() {
    local version

    version="$(
        ollama --version 2>/dev/null \
            || true
    )"

    if [[ -n "$version" ]]; then
        log_info \
            "$version"
    fi
}


main() {
    log_info \
        "Installation du moteur IA local Ollama"

    require_root

    if ! is_debian; then
        log_error \
            "Ce bootstrap OpenCoach supporte actuellement Debian uniquement."

        return 1
    fi

    install_ollama
    enable_ollama_service
    check_ollama_service
    show_ollama_version

    log_success \
        "Installation Ollama validée."
}


main "$@"
