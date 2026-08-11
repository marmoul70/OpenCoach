#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=/dev/null
source "$PROJECT_ROOT/scripts/lib/exit-codes.sh"
# shellcheck source=/dev/null
source "$PROJECT_ROOT/scripts/lib/log.sh"
# shellcheck source=/dev/null
source "$PROJECT_ROOT/scripts/lib/dependencies.sh"
# shellcheck source=/dev/null
source "$PROJECT_ROOT/scripts/lib/system.sh"
# shellcheck source=/dev/null
source "$PROJECT_ROOT/scripts/lib/package-manager.sh"

TESTS_PASSED=0
TESTS_FAILED=0

pass() {
    printf '[ OK ] %s\n' "$1"
    ((TESTS_PASSED += 1))
}

fail() {
    printf '[FAIL] %s\n' "$1"
    ((TESTS_FAILED += 1))
}

assert_success() {
    local description="$1"
    shift

    if "$@"; then
        pass "$description"
    else
        fail "$description"
    fi
}

assert_failure() {
    local description="$1"
    shift

    if "$@"; then
        fail "$description"
    else
        pass "$description"
    fi
}

echo "========================================"
echo " OpenCoach - Tests des bibliothèques"
echo "========================================"
echo

echo "[INFO] Tests système"

assert_success \
    "Debian est détecté" \
    is_debian

if [[ "$(get_debian_version)" == "13" ]]; then
    pass "Debian 13 est détecté"
else
    fail "Debian 13 est détecté"
fi

echo
echo "[INFO] Tests des dépendances"

assert_success \
    "bash est disponible" \
    require_command bash

assert_success \
    "git est disponible" \
    require_command git

assert_failure \
    "Une commande inexistante est refusée" \
    require_command command-that-does-not-exist

echo
echo "[INFO] Tests APT"

assert_success \
    "APT est opérationnel" \
    apt_is_usable

assert_success \
    "Le paquet bash est disponible" \
    package_is_available bash

assert_success \
    "Le paquet git est disponible" \
    package_is_available git

echo
echo "========================================"
echo " Résultat"
echo "========================================"
echo "Tests réussis : $TESTS_PASSED"
echo "Tests échoués : $TESTS_FAILED"
echo

if (( TESTS_FAILED > 0 )); then
    exit "$OPENCOACH_EXIT_GENERAL_ERROR"
fi

echo "[ OK ] Tous les tests sont réussis."
exit "$OPENCOACH_EXIT_SUCCESS"