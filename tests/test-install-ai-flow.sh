#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd
)"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

# Charge les fonctions sans déclencher main automatiquement.
# shellcheck disable=SC1091
source "$PROJECT_ROOT/scripts/bootstrap/install-ai.sh"

ENV_FILE="$TEMP_DIR/.env"
TRACE_FILE="$TEMP_DIR/trace"

# Aucun contrôle root ni aucune opération système réelle.
require_root() {
    :
}

install_ollama_if_missing() {
    printf 'install\n' >> "$TRACE_FILE"
}

start_ollama_service() {
    printf 'start\n' >> "$TRACE_FILE"
}

ensure_model_available() {
    printf 'model:%s\n' "$1" >> "$TRACE_FILE"
}

PASSED=0
FAILED=0

check() {
    local description="$1"
    shift

    if "$@"; then
        printf '[ OK ] %s\n' "$description"
        PASSED=$((PASSED + 1))
    else
        printf '[FAIL] %s\n' "$description" >&2
        FAILED=$((FAILED + 1))
    fi
}

test_invalid_model_stops_before_ollama() {
    printf 'OPENCOACH_AI_MODEL=invalid/model\n' > "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    : > "$TRACE_FILE"

    local status=0
    main >/dev/null 2>&1 || status=$?

    [[ "$status" -ne 0 ]] &&
        [[ ! -s "$TRACE_FILE" ]]
}

test_valid_model_runs_ollama_steps_in_order() {
    printf 'OPENCOACH_AI_MODEL=qwen3:8b\n' > "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    : > "$TRACE_FILE"

    main >/dev/null

    local expected
    expected="$(printf 'install\nstart\nmodel:qwen3:8b')"

    [[ "$(cat "$TRACE_FILE")" == "$expected" ]]
}

check "un modèle invalide interrompt le processus avant Ollama" \
    test_invalid_model_stops_before_ollama

check "un modèle valide déclenche les étapes dans le bon ordre" \
    test_valid_model_runs_ollama_steps_in_order

printf '\nTests réussis : %d\n' "$PASSED"
printf 'Tests échoués : %d\n' "$FAILED"

(( FAILED == 0 ))
