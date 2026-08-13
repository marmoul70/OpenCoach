#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$PROJECT_ROOT/scripts/bootstrap/check-environment.sh"

source "$PROJECT_ROOT/scripts/lib/exit-codes.sh"
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

assert_exit_code() {
    local expected="$1"
    local description="$2"
    shift 2

    local actual

    set +e
    "$@" >/tmp/opencoach-test-output.log 2>&1
    actual=$?
    set -e

    if [[ "$actual" == "$expected" ]]; then
        pass "$description"
    else
        fail "$description"
        printf '       Code attendu : %s\n' "$expected"
        printf '       Code obtenu  : %s\n' "$actual"
        printf '       Sortie :\n'
        sed 's/^/       /' /tmp/opencoach-test-output.log
    fi
}

echo "========================================"
echo " OpenCoach - Tests check-environment"
echo "========================================"
echo

echo "[INFO] Tests de syntaxe"

if bash -n "$SCRIPT"; then
    pass "check-environment.sh possède une syntaxe Bash valide"
else
    fail "check-environment.sh possède une syntaxe Bash valide"
fi

echo
echo "[INFO] Tests du CLI"

assert_exit_code \
    "$OPENCOACH_EXIT_SUCCESS" \
    "--help retourne un succès" \
    "$SCRIPT" --help

assert_exit_code \
    "$OPENCOACH_EXIT_INVALID_ARGUMENT" \
    "Un argument invalide est refusé" \
    "$SCRIPT" --invalid-option

assert_exit_code \
    "$OPENCOACH_EXIT_INVALID_ARGUMENT" \
    "--dev sans --install est refusé" \
    "$SCRIPT" --dev

echo
echo "[INFO] Vérification de la présence des modes"

if "$SCRIPT" --help 2>&1 | grep -q -- "--install --dev"; then
    pass "L'aide documente le mode --install --dev"
else
    fail "L'aide documente le mode --install --dev"
fi

if "$SCRIPT" --help 2>&1 | grep -q -- "--dev"; then
    pass "L'aide documente l'option --dev"
else
    fail "L'aide documente l'option --dev"
fi

echo
echo "[INFO] Tests du gestionnaire de paquets"

DRY_RUN_OUTPUT="$(install_packages --dry-run bash git shellcheck 2>&1)"
DRY_RUN_STATUS=$?

if (( DRY_RUN_STATUS == 0 )); then
    pass "Le mode dry-run du gestionnaire de paquets fonctionne"
else
    fail "Le mode dry-run du gestionnaire de paquets fonctionne"
fi

if printf '%s\n' "$DRY_RUN_OUTPUT" | grep -q "\[DRY-RUN\]"; then
    pass "Le mode dry-run indique qu'aucune installation réelle n'est effectuée"
else
    fail "Le mode dry-run indique qu'aucune installation réelle n'est effectuée"
fi

if printf '%s\n' "$DRY_RUN_OUTPUT" | grep -q "bash" &&
   printf '%s\n' "$DRY_RUN_OUTPUT" | grep -q "git" &&
   printf '%s\n' "$DRY_RUN_OUTPUT" | grep -q "shellcheck"; then
    pass "Le mode dry-run traite correctement les paquets demandés"
else
    fail "Le mode dry-run traite correctement les paquets demandés"
fi

echo
echo "========================================"
echo " Résultat"
echo "========================================"
echo "Tests réussis : $TESTS_PASSED"
echo "Tests échoués : $TESTS_FAILED"
echo

rm -f /tmp/opencoach-test-output.log

if (( TESTS_FAILED > 0 )); then
    exit "$OPENCOACH_EXIT_GENERAL_ERROR"
fi

echo "[ OK ] Tous les tests check-environment sont réussis."

exit "$OPENCOACH_EXIT_SUCCESS"