#!/usr/bin/env bash

# OpenCoach - Bootstrap principal
#
# Point d'entrée unique pour préparer une VM OpenCoach.
#
# Usage :
#   sudo ./scripts/bootstrap/install.sh
#   sudo ./scripts/bootstrap/install.sh --dev

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


DEV_REQUESTED=0


show_help() {
    printf '%s\n' "OpenCoach - Bootstrap"
    printf '\n'
    printf '%s\n' "Utilisation :"
    printf '  %s\n' "$0"
    printf '  %s --dev\n' "$0"
    printf '  %s --help\n' "$0"
    printf '\n'
    printf '%s\n' "Options :"
    printf '%s\n' \
        "  --dev    Installe également les dépendances de développement."
    printf '%s\n' \
        "  --help   Affiche cette aide."
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
                log_error \
                    "Argument inconnu : $1"

                show_help >&2

                exit 2
                ;;
        esac

        shift
    done
}


run_environment_installation() {
    local arguments=(
        "--install"
    )

    if (( DEV_REQUESTED == 1 )); then
        arguments+=(
            "--dev"
        )
    fi

    log_info \
        "Installation et validation de l'environnement OpenCoach"

    if ! "$BOOTSTRAP_DIR/check-environment.sh" \
        "${arguments[@]}"; then

        log_error \
            "Échec de la préparation de l'environnement OpenCoach."

        return 1
    fi

    log_success \
        "Environnement OpenCoach installé et validé."
}


main() {
    parse_arguments "$@"

    log_info \
        "Bootstrap OpenCoach"

    run_environment_installation

    log_success \
        "Bootstrap OpenCoach terminé avec succès."
}


main "$@"
