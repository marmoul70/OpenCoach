#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd
)"

# shellcheck source=../scripts/lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

UPGRADE_SCRIPT="$PROJECT_ROOT/scripts/bootstrap/upgrade.sh"


passed=0
failed=0


check() {
    local description="$1"
    shift

    if "$@"; then
        log_success             "$description"

        passed=$((passed + 1))
    else
        log_error             "$description"

        failed=$((failed + 1))
    fi
}


test_script_exists() {
    [[ -x "$UPGRADE_SCRIPT" ]]
}


test_help_works() {
    "$UPGRADE_SCRIPT" \
        --help \
        >/dev/null
}


test_unknown_argument_is_rejected() {
    local output
    local status

    set +e

    output="$(
        "$UPGRADE_SCRIPT" \
            --invalid-option \
            2>&1
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
        "$UPGRADE_SCRIPT" \
            2>&1
    )"

    status=$?

    set -e

    [[ "$status" -ne 0 ]] \
        && grep -Fq \
            "doit être exécuté avec sudo" \
            <<< "$output"
}


test_git_pull_is_explicit_and_fast_forward_only() {
    grep -Fq \
        '"--pull"' \
        "$UPGRADE_SCRIPT" \
        && grep -Fq \
            'pull \' \
            "$UPGRADE_SCRIPT" \
        && grep -Fq \
            -- '--ff-only' \
            "$UPGRADE_SCRIPT"
}


test_upgrade_rejects_dirty_repository() {
    grep -Fq \
        'diff \' \
        "$UPGRADE_SCRIPT" \
        && grep -Fq \
            'ls-files \' \
            "$UPGRADE_SCRIPT" \
        && grep -Fq \
            -- '--others' \
            "$UPGRADE_SCRIPT"
}


test_upgrade_backs_up_database() {
    grep -Fq \
        'backup_sqlite_database()' \
        "$UPGRADE_SCRIPT" \
        && grep -Fq \
            'source.backup' \
            "$UPGRADE_SCRIPT"
}


test_upgrade_checks_backup_integrity() {
    grep -Fq \
        'PRAGMA integrity_check' \
        "$UPGRADE_SCRIPT"
}


test_upgrade_environment_uses_install_mode() {
    grep -Fq \
        'local arguments=(' \
        "$UPGRADE_SCRIPT" \
        && grep -Fq \
            '"--install"' \
            "$UPGRADE_SCRIPT" \
        && grep -Fq \
            'check-environment.sh' \
            "$UPGRADE_SCRIPT"
}


test_upgrade_reuses_application_installer() {
    grep -Fq \
        'install-application.sh' \
        "$UPGRADE_SCRIPT"
}


test_upgrade_reuses_services_installer() {
    grep -Fq \
        'install-services.sh' \
        "$UPGRADE_SCRIPT"
}


test_upgrade_verifies_alembic_head() {
    grep -Fq \
        '"$VENV_ALEMBIC" \' \
        "$UPGRADE_SCRIPT" \
        && grep -Fq \
            'heads \' \
            "$UPGRADE_SCRIPT" \
        && grep -Fq \
            'current \' \
            "$UPGRADE_SCRIPT"
}


test_upgrade_restarts_backend() {
    grep -Fq \
        'systemctl restart \' \
        "$UPGRADE_SCRIPT" \
        && grep -Fq \
            'opencoach-backend.service' \
            "$UPGRADE_SCRIPT"
}


test_upgrade_verifies_services() {
    grep -Fq \
        'systemctl is-active' \
        "$UPGRADE_SCRIPT"
}


test_upgrade_verifies_frontend_http() {
    grep -Fq \
        '"http://127.0.0.1/"' \
        "$UPGRADE_SCRIPT"
}


test_upgrade_verifies_api_health() {
    grep -Fq \
        '"http://127.0.0.1/api/health/ready"' \
        "$UPGRADE_SCRIPT"
}


test_upgrade_retries_http_checks() {
    grep -Fq \
        'attempts: int = 10' \
        "$UPGRADE_SCRIPT" \
        && grep -Fq \
            'time.sleep' \
            "$UPGRADE_SCRIPT" \
        && grep -Fq \
            '[HTTP RETRY' \
            "$UPGRADE_SCRIPT"
}


test_upgrade_displays_server_address() {
    grep -Fq \
        'OpenCoach est accessible sur' \
        "$UPGRADE_SCRIPT"
}


check \
    "upgrade.sh est exécutable" \
    test_script_exists

check \
    "--help fonctionne" \
    test_help_works

check \
    "un argument inconnu est refusé" \
    test_unknown_argument_is_rejected

check \
    "les privilèges root sont requis" \
    test_requires_root

check \
    "git pull reste explicite et utilise --ff-only" \
    test_git_pull_is_explicit_and_fast_forward_only

check \
    "un dépôt Git sale est refusé" \
    test_upgrade_rejects_dirty_repository

check \
    "une sauvegarde SQLite précède les migrations" \
    test_upgrade_backs_up_database

check \
    "l'intégrité de la sauvegarde SQLite est vérifiée" \
    test_upgrade_checks_backup_integrity

check \
    "l'environnement d'upgrade utilise --install" \
    test_upgrade_environment_uses_install_mode

check \
    "l'upgrade réutilise install-application.sh" \
    test_upgrade_reuses_application_installer

check \
    "l'upgrade réutilise install-services.sh" \
    test_upgrade_reuses_services_installer

check \
    "la révision Alembic head est vérifiée" \
    test_upgrade_verifies_alembic_head

check \
    "le backend est redémarré après upgrade" \
    test_upgrade_restarts_backend

check \
    "l'état des services est vérifié" \
    test_upgrade_verifies_services

check \
    "le frontend HTTP est vérifié" \
    test_upgrade_verifies_frontend_http

check \
    "le readiness healthcheck est vérifié" \
    test_upgrade_verifies_api_health

check \
    "les contrôles HTTP tolèrent le démarrage du backend" \
    test_upgrade_retries_http_checks

check \
    "l'adresse d'accès est affichée" \
    test_upgrade_displays_server_address


printf '\n'
printf 'Tests réussis : %d\n' "$passed"
printf 'Tests échoués : %d\n' "$failed"

if (( failed > 0 )); then
    exit 1
fi

printf '\n'
printf '[ OK ] Tous les tests upgrade sont réussis.\n'
