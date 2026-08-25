#!/usr/bin/env bash

set -Eeuo pipefail


PROJECT_ROOT="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
    pwd
)"

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"
CONSTRAINTS_FILE="$PROJECT_ROOT/requirements/constraints.txt"

# shellcheck source=../lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"


show_help() {
    cat <<'HELP'
OpenCoach - Mise à jour des dépendances Python verrouillées

Utilisation :
  ./scripts/maintenance/update-python-dependencies.sh

Ce script :
  1. vérifie l'environnement Python OpenCoach ;
  2. régénère requirements/constraints.txt depuis pyproject.toml ;
  3. vérifie la cohérence des dépendances installées ;
  4. vérifie que le fichier de contraintes a bien été produit.

Lorsqu'une dépendance Python est ajoutée, supprimée ou modifiée
dans pyproject.toml, exécutez ce script avant de lancer les tests
et de créer le commit.
HELP
}


validate_environment() {
    if [[ ! -x "$VENV_PYTHON" ]]; then
        log_error \
            "L'environnement virtuel OpenCoach est introuvable."

        log_error \
            "Attendu : $VENV_PYTHON"

        return 1
    fi

    if [[ ! -f "$PYPROJECT_FILE" ]]; then
        log_error \
            "pyproject.toml est introuvable."

        return 1
    fi

    if ! "$VENV_PYTHON" \
        -m piptools compile \
        --version \
        >/dev/null 2>&1; then

        log_error \
            "pip-tools n'est pas installé dans l'environnement OpenCoach."

        log_error \
            "Réinstallez les dépendances de développement avec le bootstrap."

        return 1
    fi

    log_success \
        "Environnement Python validé."
}


compile_constraints() {
    log_info \
        "Régénération des dépendances Python verrouillées"

    (
        cd "$PROJECT_ROOT"

        "$VENV_PYTHON" \
            -m piptools compile \
            --all-extras \
            --all-build-deps \
            --strip-extras \
            --allow-unsafe \
            --output-file=requirements/constraints.txt \
            pyproject.toml
    )

    if [[ ! -s "$CONSTRAINTS_FILE" ]]; then
        log_error \
            "requirements/constraints.txt n'a pas été généré."

        return 1
    fi

    log_success \
        "requirements/constraints.txt régénéré."
}


validate_constraints() {
    log_info \
        "Vérification du fichier de dépendances verrouillées"

    if ! grep -Eq \
        '^[A-Za-z0-9_.-]+==[^[:space:]]+' \
        "$CONSTRAINTS_FILE"; then

        log_error \
            "Aucune dépendance verrouillée n'a été trouvée."

        return 1
    fi

    log_success \
        "Fichier de dépendances verrouillées valide."
}


check_installed_dependencies() {
    log_info \
        "Vérification des dépendances Python actuellement installées"

    "$VENV_PYTHON" \
        -m pip \
        check

    log_success \
        "Dépendances Python installées cohérentes."
}


main() {
    case "${1:-}" in
        "")
            ;;
        -h|--help)
            show_help
            return 0
            ;;
        *)
            log_error \
                "Argument inconnu : $1"

            show_help

            return 2
            ;;
    esac

    log_info \
        "Mise à jour des dépendances Python OpenCoach"

    validate_environment
    compile_constraints
    validate_constraints
    check_installed_dependencies

    log_success \
        "Dépendances Python verrouillées mises à jour."

    log_info \
        "Lancez maintenant les tests OpenCoach avant le commit."
}


main "$@"
