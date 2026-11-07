#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$PROJECT_ROOT/scripts/deploy-frontend.sh"

passed=0
failed=0

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

test_script_exists() {
    [[ -f "$SCRIPT" ]]
}

test_build_runs_before_privileged_deployment() {
    local build_line sudo_line
    build_line="$(grep -nF 'npm run build' "$SCRIPT" | head -n 1 | cut -d: -f1)"
    sudo_line="$(grep -nF 'sudo -v' "$SCRIPT" | head -n 1 | cut -d: -f1)"
    [[ -n "$build_line" && -n "$sudo_line" && "$build_line" -lt "$sudo_line" ]]
}

test_build_failure_stops_deployment() {
    grep -Fq 'La compilation a échoué. Aucun déploiement effectué.' "$SCRIPT"
}

test_build_output_is_validated() {
    grep -Fq "[[ -s \"\$DIST_DIR/index.html\" ]]" "$SCRIPT" \
        && grep -Fq "[[ -d \"\$DIST_DIR/assets\" ]]" "$SCRIPT" \
        && grep -Fq 'Aucun fichier JS/CSS référencé' "$SCRIPT"
}

test_referenced_assets_are_checked_before_copy() {
    local validation_line copy_line
    validation_line="$(grep -nF "[[ -s \"\$DIST_DIR/\$asset\" ]]" "$SCRIPT" | head -n 1 | cut -d: -f1)"
    copy_line="$(grep -nF 'sudo cp -a' "$SCRIPT" | head -n 1 | cut -d: -f1)"
    [[ -n "$validation_line" && -n "$copy_line" && "$validation_line" -lt "$copy_line" ]]
}

test_deployed_index_is_compared() {
    grep -Fq "cmp -s \"\$DIST_DIR/index.html\" \"\$WEB_ROOT/index.html\"" "$SCRIPT"
}

test_deployed_assets_are_checked() {
    grep -Fq "sudo test -s \"\$WEB_ROOT/\$asset\"" "$SCRIPT"
}

test_nginx_config_is_validated_before_reload() {
    local config_line reload_line
    config_line="$(grep -nF 'sudo nginx -t' "$SCRIPT" | head -n 1 | cut -d: -f1)"
    reload_line="$(grep -nF 'sudo systemctl reload nginx' "$SCRIPT" | head -n 1 | cut -d: -f1)"
    [[ -n "$config_line" && -n "$reload_line" && "$config_line" -lt "$reload_line" ]]
}

test_only_nginx_is_reloaded() {
    grep -Fq 'sudo systemctl reload nginx' "$SCRIPT" \
        && ! grep -Eq 'systemctl (restart|reload) opencoach-backend' "$SCRIPT"
}

test_shellcheck_source_path_is_relative_to_script() {
    grep -Fq '# shellcheck source=./lib/log.sh' "$SCRIPT"
}

check "le script de déploiement frontend existe" test_script_exists
check "le build s'exécute avant toute élévation sudo" test_build_runs_before_privileged_deployment
check "un échec de build bloque le déploiement" test_build_failure_stops_deployment
check "les artefacts du build sont validés" test_build_output_is_validated
check "les assets référencés sont vérifiés avant copie" test_referenced_assets_are_checked_before_copy
check "le index.html déployé est comparé au build" test_deployed_index_is_compared
check "les assets déployés sont contrôlés" test_deployed_assets_are_checked
check "Nginx est validé avant son rechargement" test_nginx_config_is_validated_before_reload
check "aucun redémarrage du backend n'est déclenché" test_only_nginx_is_reloaded
check "le chemin ShellCheck de la librairie de logs est cohérent" test_shellcheck_source_path_is_relative_to_script

printf '\nTests réussis : %d\n' "$passed"
printf 'Tests échoués : %d\n' "$failed"

if (( failed > 0 )); then
    exit 1
fi

printf '\n[ OK ] Tous les tests de déploiement frontend sont réussis.\n'
