#!/usr/bin/env bash

# OpenCoach - Lanceur du backend de développement.
#
# Charge automatiquement le fichier .env avant de démarrer Uvicorn.

set -Eeuo pipefail


SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd -- "$SCRIPT_DIR/../.."
    pwd
)"


# shellcheck source=scripts/lib/environment.sh
source "$PROJECT_ROOT/scripts/lib/environment.sh"


load_and_validate_opencoach_environment \
    "$PROJECT_ROOT"


VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
    printf '%s\n' \
        "ERREUR : environnement virtuel OpenCoach introuvable." \
        >&2

    printf '%s\n' \
        "Attendu : $VENV_PYTHON" \
        >&2

    exit 1
fi


cd "$PROJECT_ROOT"

exec "$VENV_PYTHON" -m uvicorn \
    opencoach.api.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
