#!/usr/bin/env bash

# OpenCoach - Bootstrap principal
#
# Point d'entrée unique pour préparer une VM OpenCoach.
#
# Usage :
#   sudo ./scripts/bootstrap/install.sh

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


run_step() {
    local description="$1"
    local script_path="$2"

    log_info "$description"

    if ! "$script_path"; then
        log_error \
            "Échec : $description"

        return 1
    fi

    log_success \
        "$description terminé."
}


main() {
    log_info \
        "Bootstrap OpenCoach"

    run_step \
        "Validation de l'environnement" \
        "$BOOTSTRAP_DIR/check-environment.sh"

    run_step \
        "Installation du moteur IA local Ollama" \
        "$BOOTSTRAP_DIR/install-ollama.sh"

    run_step \
        "Installation du modèle IA OpenCoach" \
        "$BOOTSTRAP_DIR/install-ollama-model.sh"

    log_success \
        "Bootstrap OpenCoach terminé avec succès."
}


main "$@"
