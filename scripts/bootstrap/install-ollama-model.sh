#!/usr/bin/env bash

# OpenCoach - Installation du modèle IA Ollama
#
# Vérifie et installe le modèle local utilisé par OpenCoach.
# Le script est idempotent.
#
# Variables configurables :
#   OPENCOACH_OLLAMA_MODEL
#
# Exemple :
#   OPENCOACH_OLLAMA_MODEL=qwen3:8b \
#       sudo -E ./scripts/bootstrap/install-ollama-model.sh

set -Eeuo pipefail


BOOTSTRAP_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd -- "$BOOTSTRAP_DIR/../.."
    pwd
)"

# shellcheck source=scripts/lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

# shellcheck source=scripts/lib/system.sh
source "$PROJECT_ROOT/scripts/lib/system.sh"


OPENCOACH_OLLAMA_MODEL="${OPENCOACH_OLLAMA_MODEL:-Jadio/Qwen3_4b_instruct_q4km:latest}"


require_ollama() {
    if ! command -v ollama >/dev/null 2>&1; then
        log_error \
            "Ollama n'est pas installé."

        return 1
    fi
}


require_ollama_service() {
    require_command systemctl

    if ! systemctl is-active \
        --quiet \
        ollama
    then
        log_error \
            "Le service Ollama n'est pas actif."

        return 1
    fi
}


is_model_installed() {
    ollama list \
        | awk 'NR > 1 {print $1}' \
        | grep -Fxq \
            "$OPENCOACH_OLLAMA_MODEL"
}


install_model() {
    if is_model_installed; then
        log_success \
            "Modèle Ollama déjà installé : $OPENCOACH_OLLAMA_MODEL"

        return 0
    fi

    log_info \
        "Téléchargement du modèle Ollama : $OPENCOACH_OLLAMA_MODEL"

    ollama pull \
        "$OPENCOACH_OLLAMA_MODEL"

    if ! is_model_installed; then
        log_error \
            "Le modèle Ollama n'est pas disponible après téléchargement."

        return 1
    fi

    log_success \
        "Modèle Ollama installé : $OPENCOACH_OLLAMA_MODEL"
}


main() {
    log_info \
        "Configuration du modèle IA OpenCoach"

    require_ollama
    require_ollama_service
    install_model

    log_success \
        "Modèle IA OpenCoach prêt."
}


main "$@"
