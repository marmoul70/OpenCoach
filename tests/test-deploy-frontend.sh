#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$PROJECT_ROOT/scripts/deploy-frontend.sh"
LEGACY_SCRIPT="$PROJECT_ROOT/scripts/deploy_frontend.sh"

passed=0
failed=0

check() {
    local description="$1"
    shift
    if "$@"; then
        printf '[ OK ] %s\n' "$description"
        ((passed += 1))
    else
        printf '[FAIL] %s\n' "$description" >&2
        ((failed += 1))
    fi
}

test_scripts_exist() {
    [[ -f "$SCRIPT" && -f "$LEGACY_SCRIPT" ]]
}

test_project_root_is_resolved_from_script_location() {
    grep -Fq "dirname -- \"\${BASH_SOURCE[0]}\"" "$SCRIPT" \
        && ! grep -Fq "\$HOME/Projects/OpenCoach" "$SCRIPT"
}

test_locked_frontend_install_and_checks_run_before_privileged_deployment() {
    local npm_ci lint build sudo_line
    npm_ci="$(grep -nF 'npm ci' "$SCRIPT" | head -n1 | cut -d: -f1)"
    lint="$(grep -nF 'npm run lint' "$SCRIPT" | head -n1 | cut -d: -f1)"
    build="$(grep -nF 'npm run build' "$SCRIPT" | head -n1 | cut -d: -f1)"
    sudo_line="$(grep -nF 'sudo -v' "$SCRIPT" | head -n1 | cut -d: -f1)"
    [[ -n "$npm_ci" && -n "$lint" && -n "$build" && -n "$sudo_line" ]] \
        && (( npm_ci < sudo_line && lint < sudo_line && build < sudo_line ))
}

test_failed_build_stops_before_deployment() {
    grep -Fq 'Aucun déploiement effectué.' "$SCRIPT"
}

test_bootstrap_can_reuse_prebuilt_frontend() {
    grep -Fq 'OPENCOACH_FRONTEND_PREBUILT' "$SCRIPT"
}

test_root_execution_builds_as_project_owner() {
    grep -Fq "runuser -u \"\$PROJECT_USER\" -- \"\$@\"" "$SCRIPT"
}

test_release_metadata_is_created() {
    grep -Fq 'version.json' "$SCRIPT" \
        && grep -Fq '"built_at"' "$SCRIPT"
}

test_release_is_staged_before_atomic_switch() {
    local staging copy move switch
    staging="$(grep -nF 'run_privileged mktemp -d' "$SCRIPT" | head -n1 | cut -d: -f1)"
    copy="$(grep -nF "run_privileged cp -a \"\$DIST_DIR/.\"" "$SCRIPT" | head -n1 | cut -d: -f1)"
    move="$(grep -nF "run_privileged mv \"\$STAGING_DIR\" \"\$RELEASE_DIR\"" "$SCRIPT" | head -n1 | cut -d: -f1)"
    switch="$(grep -nF "sudo mv -Tf \"\$TMP_LINK\" \"\$CURRENT_LINK\"" "$SCRIPT" | head -n1 | cut -d: -f1)"
    [[ -n "$staging" && -n "$copy" && -n "$move" && -n "$switch" ]] \
        && (( staging < copy && copy < move && move < switch ))
}

test_rollback_is_available_for_failed_nginx_validation_or_reload() {
    grep -Fq "rollback_current \"\$PREVIOUS_TARGET\"" "$SCRIPT" \
        && grep -Fq 'run_privileged nginx -t' "$SCRIPT" \
        && grep -Fq 'run_privileged systemctl reload nginx' "$SCRIPT"
}

test_web_root_is_configurable() {
    grep -Fq 'OPENCOACH_WEB_ROOT:-/var/www/opencoach' "$SCRIPT"
}

test_no_backend_restart_is_triggered() {
    ! grep -Eq 'systemctl (restart|reload) opencoach-backend' "$SCRIPT"
}

test_legacy_script_delegates_to_canonical_script() {
    grep -Fq "exec \"\$SCRIPT_DIR/deploy-frontend.sh\" \"\$@\"" "$LEGACY_SCRIPT"
}

test_shellcheck_source_is_declared() {
    grep -Fq '# shellcheck source=scripts/lib/log.sh' "$SCRIPT"
}

check "les deux points d'entrée de déploiement existent" test_scripts_exist
check "le chemin du projet est calculé depuis le script" test_project_root_is_resolved_from_script_location
check "npm ci, lint et build précèdent les opérations privilégiées" test_locked_frontend_install_and_checks_run_before_privileged_deployment
check "un échec de build bloque le déploiement" test_failed_build_stops_before_deployment
check "le bootstrap peut réutiliser le frontend déjà compilé" test_bootstrap_can_reuse_prebuilt_frontend
check "une exécution root construit sous le propriétaire du dépôt" test_root_execution_builds_as_project_owner
check "les métadonnées de release sont créées" test_release_metadata_is_created
check "la release est préparée avant la bascule atomique" test_release_is_staged_before_atomic_switch
check "un rollback est prévu si Nginx échoue" test_rollback_is_available_for_failed_nginx_validation_or_reload
check "la racine web peut être configurée" test_web_root_is_configurable
check "le déploiement ne redémarre pas le backend" test_no_backend_restart_is_triggered
check "l'ancien nom de script délègue au point d'entrée canonique" test_legacy_script_delegates_to_canonical_script
check "la dépendance ShellCheck est déclarée" test_shellcheck_source_is_declared

printf '\nTests réussis : %d\n' "$passed"
printf 'Tests échoués : %d\n' "$failed"

if (( failed > 0 )); then
    exit 1
fi

printf '\n[ OK ] Tous les tests de déploiement frontend sont réussis.\n'
