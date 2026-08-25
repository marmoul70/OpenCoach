#!/usr/bin/env bash

set -Eeuo pipefail


PROJECT_ROOT="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd
)"

SCRIPT="$PROJECT_ROOT/scripts/maintenance/update-python-dependencies.sh"

PASSED=0
FAILED=0


ok() {
    printf '[ OK ] %s\n' "$1"
}


fail() {
    printf '[FAIL] %s\n' "$1" >&2
}


check() {
    local description="$1"
    local test_function="$2"

    if "$test_function"; then
        ok "$description"
        PASSED=$((PASSED + 1))
    else
        fail "$description"
        FAILED=$((FAILED + 1))
    fi
}


test_script_is_executable() {
    [[ -x "$SCRIPT" ]]
}


test_help_works() {
    "$SCRIPT" \
        --help \
        >/dev/null
}


test_unknown_argument_is_rejected() {
    if "$SCRIPT" \
        --invalid-option \
        >/dev/null 2>&1; then

        return 1
    fi

    return 0
}


test_uses_opencoach_logs() {
    grep -Fq \
        'scripts/lib/log.sh' \
        "$SCRIPT"
}


test_uses_pyproject() {
    grep -Fq \
        'pyproject.toml' \
        "$SCRIPT"
}


test_uses_constraints_file() {
    grep -Fq \
        'requirements/constraints.txt' \
        "$SCRIPT"
}


test_uses_piptools() {
    grep -Fq \
        'piptools compile' \
        "$SCRIPT"
}


test_locks_all_extras() {
    grep -Fq \
        -- '--all-extras' \
        "$SCRIPT"
}


test_locks_build_dependencies() {
    grep -Fq \
        -- '--all-build-deps' \
        "$SCRIPT"
}


test_includes_unsafe_dependencies() {
    grep -Fq \
        -- '--allow-unsafe' \
        "$SCRIPT"
}


test_strips_extras() {
    grep -Fq \
        -- '--strip-extras' \
        "$SCRIPT"
}


test_uses_portable_paths() {
    if grep -Fq \
        '/home/opencoach/' \
        "$SCRIPT"; then

        return 1
    fi

    grep -Fq \
        -- '--output-file=requirements/constraints.txt' \
        "$SCRIPT" \
        && grep -Fq \
            'pyproject.toml' \
            "$SCRIPT"
}


test_checks_generated_file() {
    grep -Fq \
        '[[ ! -s "$CONSTRAINTS_FILE" ]]' \
        "$SCRIPT"
}


test_checks_locked_packages() {
    grep -Fq \
        "'^[A-Za-z0-9_.-]+==[^[:space:]]+'" \
        "$SCRIPT"
}


test_runs_pip_check() {
    grep -Fq \
        -e '-m pip \' \
        "$SCRIPT" \
        && grep -Fq \
            'check' \
            "$SCRIPT"
}


echo "========================================"
echo " OpenCoach - Tests dépendances Python"
echo "========================================"
echo

check \
    "update-python-dependencies.sh est exécutable" \
    test_script_is_executable

check \
    "--help fonctionne" \
    test_help_works

check \
    "un argument inconnu est refusé" \
    test_unknown_argument_is_rejected

check \
    "la librairie de logs OpenCoach est utilisée" \
    test_uses_opencoach_logs

check \
    "pyproject.toml est utilisé comme source" \
    test_uses_pyproject

check \
    "requirements/constraints.txt est utilisé comme lock" \
    test_uses_constraints_file

check \
    "pip-tools est utilisé pour générer le lock" \
    test_uses_piptools

check \
    "tous les extras Python sont verrouillés" \
    test_locks_all_extras

check \
    "les dépendances de build sont verrouillées" \
    test_locks_build_dependencies

check \
    "pip et setuptools sont verrouillables" \
    test_includes_unsafe_dependencies

check \
    "les extras sont aplatis dans le lock" \
    test_strips_extras

check \
    "la génération du lock utilise des chemins portables" \
    test_uses_portable_paths

check \
    "le fichier généré est contrôlé" \
    test_checks_generated_file

check \
    "la présence de versions verrouillées est contrôlée" \
    test_checks_locked_packages

check \
    "pip check valide les dépendances installées" \
    test_runs_pip_check


echo
echo "Tests réussis : $PASSED"
echo "Tests échoués : $FAILED"
echo

if (( FAILED > 0 )); then
    fail \
        "Des tests update-python-dependencies ont échoué."

    exit 1
fi

ok \
    "Tous les tests update-python-dependencies sont réussis."
