#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd
)"

INSTALL_SCRIPT="$PROJECT_ROOT/scripts/bootstrap/install-ai.sh"
TEMP_DIR="$(mktemp -d)"

passed=0
failed=0

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

check() {
    local description="$1"
    shift

    if "$@"; then
        printf '[ OK ] %s\n' "$description"
        passed=$((passed + 1))
    else
        printf '[FAIL] %s\n' "$description" >&2
        failed=$((failed + 1))
    fi
}

prepare_env() {
    local content="$1"
    local target="$TEMP_DIR/.env"

    printf '%s\n' "$content" > "$target"
    chmod 600 "$target"
}

run_env_python() {
    local target="$TEMP_DIR/.env"

    python3 - "$INSTALL_SCRIPT" "$target" <<'PY'
import re
import subprocess
import sys
from pathlib import Path

script = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(
    r"if ! python3 - \"\$ENV_FILE\" \"\$DEFAULT_MODEL\" <<'PYTHON'\n"
    r"(.*?)\nPYTHON\n    then",
    script,
    re.S,
)

if not match:
    raise SystemExit("Bloc Python de configuration introuvable.")

program = match.group(1)
result = subprocess.run(
    [sys.executable, "-", sys.argv[2], "phi4-mini:latest"],
    input=program,
    text=True,
    capture_output=True,
)

if result.stdout:
    print(result.stdout, end="")
if result.stderr:
    print(result.stderr, end="", file=sys.stderr)

raise SystemExit(result.returncode)
PY
}

test_adds_missing_settings() {
    prepare_env "OPENCOACH_SECRET_KEY=test-secret"
    run_env_python

    grep -q '^OPENCOACH_AI_ENABLED=false$' "$TEMP_DIR/.env" &&
    grep -q '^OPENCOACH_AI_PROVIDER=ollama$' "$TEMP_DIR/.env" &&
    grep -q '^OPENCOACH_AI_MODEL=phi4-mini:latest$' "$TEMP_DIR/.env"
}

test_preserves_existing_values() {
    prepare_env "$(printf '%s\n' \
        'OPENCOACH_SECRET_KEY=my-secret' \
        'OPENCOACH_AI_ENABLED=true' \
        'OPENCOACH_AI_MODEL=qwen3:8b')"

    run_env_python

    grep -q '^OPENCOACH_SECRET_KEY=my-secret$' "$TEMP_DIR/.env" &&
    grep -q '^OPENCOACH_AI_ENABLED=true$' "$TEMP_DIR/.env" &&
    grep -q '^OPENCOACH_AI_MODEL=qwen3:8b$' "$TEMP_DIR/.env"
}

test_refuses_duplicate_keys_without_modification() {
    prepare_env "$(printf '%s\n' \
        'OPENCOACH_AI_MODEL=qwen3:8b' \
        'OPENCOACH_AI_MODEL=phi4-mini:latest')"

    local before
    before="$(sha256sum "$TEMP_DIR/.env")"

    if run_env_python; then
        return 1
    fi

    local after
    after="$(sha256sum "$TEMP_DIR/.env")"

    [[ "$before" == "$after" ]]
}

test_is_idempotent() {
    prepare_env "OPENCOACH_SECRET_KEY=test-secret"

    run_env_python
    local before
    before="$(sha256sum "$TEMP_DIR/.env")"

    run_env_python
    local after
    after="$(sha256sum "$TEMP_DIR/.env")"

    [[ "$before" == "$after" ]]
}

test_fills_empty_value() {
    prepare_env "OPENCOACH_AI_MODEL="

    run_env_python

    grep -q '^OPENCOACH_AI_MODEL=phi4-mini:latest$' "$TEMP_DIR/.env"
}

test_sets_secure_permissions() {
    prepare_env "OPENCOACH_SECRET_KEY=test-secret"
    chmod 644 "$TEMP_DIR/.env"

    run_env_python

    [[ "$(stat -c '%a' "$TEMP_DIR/.env")" == "600" ]]
}

check "Ajout des paramètres IA manquants" test_adds_missing_settings
check "Préservation des valeurs personnalisées et secrets" test_preserves_existing_values
check "Refus des doublons sans modification du fichier" test_refuses_duplicate_keys_without_modification
check "Relance idempotente" test_is_idempotent
check "Remplacement des valeurs vides" test_fills_empty_value
check "Permissions .env à 600" test_sets_secure_permissions

printf '\nTests réussis : %d\n' "$passed"
printf 'Tests échoués : %d\n' "$failed"

(( failed == 0 ))
