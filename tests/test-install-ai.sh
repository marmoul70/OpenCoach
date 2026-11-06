#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd
)"

INSTALL_SCRIPT="$PROJECT_ROOT/scripts/bootstrap/install.sh"
AI_INSTALL_SCRIPT="$PROJECT_ROOT/scripts/bootstrap/install-ai.sh"
PACKAGES_FILE="$PROJECT_ROOT/scripts/lib/packages.sh"
COMMANDS_FILE="$PROJECT_ROOT/scripts/lib/dependencies.sh"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"

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

test_ai_installer_exists() {
    [[ -f "$AI_INSTALL_SCRIPT" ]]
}

test_ai_help_works() {
    bash "$AI_INSTALL_SCRIPT" --help >/dev/null
}

test_ai_unknown_argument_is_rejected() {
    local status=0
    bash "$AI_INSTALL_SCRIPT" --invalid-option >/dev/null 2>&1 || status=$?
    [[ "$status" -eq 2 ]]
}

test_main_installer_exposes_opt_in_flag() {
    grep -Fq -- '--with-ai' "$INSTALL_SCRIPT"
}

test_main_installer_calls_ai_installer_only_when_requested() {
    grep -Fq 'WITH_AI_REQUESTED == 1' "$INSTALL_SCRIPT" \
        && grep -Fq 'bash "$BOOTSTRAP_DIR/install-ai.sh"' "$INSTALL_SCRIPT"
}

test_curl_is_declared_as_system_package_and_command() {
    grep -Fxq '    curl' "$PACKAGES_FILE" \
        && grep -Fxq '    curl' "$COMMANDS_FILE"
}

test_ollama_is_optional_not_a_required_system_package() {
    ! grep -Eq '^[[:space:]]*ollama[[:space:]]*$' "$PACKAGES_FILE"
}

test_ai_is_disabled_by_default() {
    grep -Fxq 'OPENCOACH_AI_ENABLED=false' "$ENV_EXAMPLE" \
        && grep -Fq 'OPENCOACH_AI_ENABLED' "$AI_INSTALL_SCRIPT"
}

test_ollama_is_local_only() {
    grep -Fq 'http://127.0.0.1:11434' "$AI_INSTALL_SCRIPT" \
        && grep -Fq 'http://127.0.0.1:11434' "$ENV_EXAMPLE"
}

test_existing_httpx_is_available_for_local_api() {
    grep -Fq '"httpx>=0.28,<1"' "$PYPROJECT_FILE"
}

test_ai_installer_does_not_modify_backend_service() {
    ! grep -Eq 'systemctl (restart|stop) opencoach-backend' "$AI_INSTALL_SCRIPT"
}

echo "========================================"
echo " OpenCoach - Tests installation IA locale"
echo "========================================"
echo

check "le script d'installation IA existe" test_ai_installer_exists
check "--help du script IA fonctionne" test_ai_help_works
check "un argument inconnu est refusé" test_ai_unknown_argument_is_rejected
check "install.sh expose l'option --with-ai" test_main_installer_exposes_opt_in_flag
check "l'installation IA est strictement optionnelle" test_main_installer_calls_ai_installer_only_when_requested
check "curl est déclaré comme paquet et commande système" test_curl_is_declared_as_system_package_and_command
check "Ollama n'est pas une dépendance système obligatoire" test_ollama_is_optional_not_a_required_system_package
check "l'IA est désactivée par défaut" test_ai_is_disabled_by_default
check "l'API Ollama est configurée en local uniquement" test_ollama_is_local_only
check "httpx est déjà déclaré comme dépendance Python" test_existing_httpx_is_available_for_local_api
check "le bootstrap IA ne stoppe ni ne redémarre le backend" test_ai_installer_does_not_modify_backend_service

echo
echo "Tests réussis : $PASSED"
echo "Tests échoués : $FAILED"

if (( FAILED > 0 )); then
    exit 1
fi

printf '\n[ OK ] Tous les tests d'installation IA sont réussis.\n'
