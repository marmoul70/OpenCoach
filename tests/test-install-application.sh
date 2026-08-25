#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd
)"

SCRIPT="$PROJECT_ROOT/scripts/bootstrap/install-application.sh"


tests_passed=0
tests_failed=0


assert_success() {
    local description="$1"

    shift

    if "$@"; then
        printf '[ OK ] %s\n' "$description"
        tests_passed=$((tests_passed + 1))
    else
        printf '[FAIL] %s\n' "$description" >&2
        tests_failed=$((tests_failed + 1))
    fi
}


assert_contains() {
    local description="$1"
    local expected="$2"
    local actual="$3"

    if grep -Fq -- "$expected" <<< "$actual"; then
        printf '[ OK ] %s\n' "$description"
        tests_passed=$((tests_passed + 1))
    else
        printf '[FAIL] %s\n' "$description" >&2
        printf '       attendu : %s\n' "$expected" >&2
        tests_failed=$((tests_failed + 1))
    fi
}


test_script_exists() {
    [[ -x "$SCRIPT" ]]
}


test_help_works() {
    "$SCRIPT" --help >/dev/null
}


test_unknown_argument_is_rejected() {
    local output
    local status

    set +e

    output="$(
        "$SCRIPT" --invalid-option 2>&1
    )"

    status=$?

    set -e

    [[ "$status" -eq 2 ]] \
        && grep -Fqi \
            "argument inconnu" \
            <<< "$output"
}


test_requires_root() {
    if (( EUID == 0 )); then
        return 0
    fi

    local output
    local status

    set +e

    output="$(
        "$SCRIPT" 2>&1
    )"

    status=$?

    set -e

    [[ "$status" -ne 0 ]] \
        && grep -Fq \
            "doit être exécuté avec sudo" \
            <<< "$output"
}


test_logging_library_is_used() {
    grep -Fq \
        'source "$PROJECT_ROOT/scripts/lib/log.sh"' \
        "$SCRIPT"
}


test_python_venv_is_declared() {
    grep -Fq \
        'python3' \
        "$PROJECT_ROOT/scripts/lib/packages.sh" \
        && grep -Fq \
            'python3-venv' \
            "$PROJECT_ROOT/scripts/lib/packages.sh"
}


test_frontend_install_uses_npm_ci() {
    grep -Fq \
        'npm ci' \
        "$SCRIPT"
}


test_alembic_upgrade_is_present() {
    grep -Fq \
        'upgrade' \
        "$SCRIPT" \
        && grep -Fq \
            'head' \
            "$SCRIPT"
}


assert_success \
    "install-application.sh est exécutable" \
    test_script_exists

assert_success \
    "--help fonctionne" \
    test_help_works

assert_success \
    "un argument inconnu est refusé" \
    test_unknown_argument_is_rejected

assert_success \
    "les privilèges root sont requis" \
    test_requires_root

assert_success \
    "la librairie de logs OpenCoach est utilisée" \
    test_logging_library_is_used

assert_success \
    "Python et python3-venv sont déclarés" \
    test_python_venv_is_declared

assert_success \
    "le frontend utilise npm ci" \
    test_frontend_install_uses_npm_ci

assert_success \
    "les migrations Alembic sont appliquées" \
    test_alembic_upgrade_is_present


printf '\n'
printf 'Tests réussis : %d\n' "$tests_passed"
printf 'Tests échoués : %d\n' "$tests_failed"

if (( tests_failed > 0 )); then
    exit 1
fi

printf '\n'
printf '[ OK ] Tous les tests install-application sont réussis.\n'
