#!/usr/bin/env bash

# OpenCoach - Déploiement frontend par releases atomiques.
#
# Usage :
#   ./scripts/deploy-frontend.sh
#
# Le script peut être lancé par le propriétaire du projet ou par root
# depuis les scripts bootstrap. Le build reste toujours exécuté sous
# l'identité du propriétaire du dépôt.

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DIST_DIR="$FRONTEND_DIR/dist"
WEB_ROOT="${OPENCOACH_WEB_ROOT:-/var/www/opencoach}"
RELEASES_DIR="$WEB_ROOT/releases"
CURRENT_LINK="$WEB_ROOT/current"
KEEP_RELEASES=5
PROJECT_USER="$(stat -c '%U' "$PROJECT_ROOT")"
STAGING_DIR=""
PREVIOUS_TARGET=""
SWITCHED=0
DEPLOY_SUCCEEDED=0

# shellcheck source=scripts/lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

fail() {
    log_error "$1"
    exit 1
}

run_as_project_owner() {
    if (( EUID == 0 )); then
        runuser -u "$PROJECT_USER" -- "$@"
    else
        "$@"
    fi
}

run_privileged() {
    if (( EUID == 0 )); then
        "$@"
    else
        sudo "$@"
    fi
}

rollback_current() {
    local previous_target="$1"
    local rollback_link="$WEB_ROOT/.current-rollback"

    if [[ -n "$previous_target" ]]; then
        run_privileged ln -sfn "$previous_target" "$rollback_link"
        run_privileged mv -Tf "$rollback_link" "$CURRENT_LINK"
    else
        run_privileged rm -f "$CURRENT_LINK"
    fi

    if run_privileged nginx -t; then
        if run_privileged systemctl is-active --quiet nginx; then
            run_privileged systemctl reload nginx || true
        else
            run_privileged systemctl start nginx || true
        fi
    fi
}

cleanup() {
    local status=$?
    trap - EXIT
    if [[ -n "$STAGING_DIR" ]]; then
        run_privileged rm -rf -- "$STAGING_DIR" || true
    fi
    if (( SWITCHED == 1 && DEPLOY_SUCCEEDED == 0 )); then
        log_warning "Déploiement interrompu : restauration de la release précédente."
        rollback_current "$PREVIOUS_TARGET" || true
    fi
    exit "$status"
}
trap cleanup EXIT

command -v node >/dev/null 2>&1 || fail "Node.js est requis."
command -v npm >/dev/null 2>&1 || fail "npm est requis."
[[ "$WEB_ROOT" == /* ]] || fail "OPENCOACH_WEB_ROOT doit être un chemin absolu."
[[ "$PROJECT_USER" != "root" ]] || fail "Le dépôt OpenCoach ne doit pas appartenir à root."
if (( EUID != 0 )) && [[ "$PROJECT_USER" != "$(id -un)" ]]; then
    fail "Lancez le déploiement avec le propriétaire du dépôt : $PROJECT_USER"
fi
[[ -f "$PROJECT_ROOT/VERSION" ]] || fail "Fichier VERSION introuvable."
[[ -f "$FRONTEND_DIR/package.json" ]] || fail "Projet frontend introuvable."
[[ -f "$FRONTEND_DIR/package-lock.json" ]] || fail "package-lock.json introuvable."

VERSION="$(tr -d '[:space:]' < "$PROJECT_ROOT/VERSION")"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9.-]+)?$ ]] || fail "Version applicative invalide : $VERSION"

if [[ -n "$(git -c safe.directory="$PROJECT_ROOT" -C "$PROJECT_ROOT" status --porcelain)" ]]; then
    log_error "Le dépôt Git contient des modifications non validées."
    git -c safe.directory="$PROJECT_ROOT" -C "$PROJECT_ROOT" status --short
    fail "Committez ou annulez les modifications avant le déploiement."
fi

GIT_SHA="$(git -c safe.directory="$PROJECT_ROOT" -C "$PROJECT_ROOT" rev-parse --short=7 HEAD)"
RELEASE_NAME="${VERSION}-${GIT_SHA}"
RELEASE_DIR="$RELEASES_DIR/$RELEASE_NAME"

log_info "Version : $VERSION"
log_info "Commit : $GIT_SHA"
log_info "Cible : $WEB_ROOT"

if [[ "${OPENCOACH_FRONTEND_PREBUILT:-0}" == "1" ]]; then
    log_info "Frontend déjà compilé par install-application.sh : lint et validation des artefacts."
    (
        cd "$FRONTEND_DIR"
        run_as_project_owner npm run lint
    ) || fail "Le lint frontend a échoué. Aucun déploiement effectué."
else
    log_info "Installation déterministe et validation du frontend..."
    (
        cd "$FRONTEND_DIR"
        run_as_project_owner npm ci
        run_as_project_owner npm run lint
        run_as_project_owner npm run build
    ) || fail "Installation, lint ou compilation frontend en échec. Aucun déploiement effectué."
fi

[[ -s "$DIST_DIR/index.html" ]] || fail "Build invalide : index.html absent."
[[ -d "$DIST_DIR/assets" ]] || fail "Build invalide : dossier assets absent."

mapfile -t ASSET_PATHS < <(
    grep -oE 'assets/[^"]+\.(js|css)' "$DIST_DIR/index.html" | sort -u
)
(("${#ASSET_PATHS[@]}" > 0)) || fail "Aucun fichier JS/CSS référencé dans index.html."

for asset in "${ASSET_PATHS[@]}"; do
    [[ -s "$DIST_DIR/$asset" ]] || fail "Asset compilé manquant : $asset"
done

log_success "Build et assets validés."
if (( EUID != 0 )); then
    sudo -v
fi
run_privileged install -d -m 755 "$RELEASES_DIR"

if [[ -e "$CURRENT_LINK" && ! -L "$CURRENT_LINK" ]]; then
    fail "$CURRENT_LINK existe mais n'est pas un lien symbolique. Déploiement annulé."
fi

if [[ -L "$CURRENT_LINK" ]]; then
    PREVIOUS_TARGET="$(readlink "$CURRENT_LINK")"
fi

if [[ ! -d "$RELEASE_DIR" ]]; then
    STAGING_DIR="$(run_privileged mktemp -d "$RELEASES_DIR/.staging.XXXXXX")"
    run_privileged cp -a "$DIST_DIR/." "$STAGING_DIR/"
    BUILD_TIME="$(date --utc '+%Y-%m-%dT%H:%M:%SZ')"
    cat <<JSON | run_privileged tee "$STAGING_DIR/version.json" >/dev/null
{
  "application": "OpenCoach",
  "version": "$VERSION",
  "commit": "$GIT_SHA",
  "built_at": "$BUILD_TIME"
}
JSON
    run_privileged test -s "$STAGING_DIR/index.html" || fail "index.html absent de la release temporaire."
    run_privileged test -s "$STAGING_DIR/version.json" || fail "version.json absent de la release temporaire."
    run_privileged mv "$STAGING_DIR" "$RELEASE_DIR"
    STAGING_DIR=""
else
    log_info "Release déjà présente : réutilisation de $RELEASE_NAME"
fi

TMP_LINK="$WEB_ROOT/.current-new"
run_privileged rm -f "$TMP_LINK"
run_privileged ln -s "releases/$RELEASE_NAME" "$TMP_LINK"
run_privileged mv -Tf "$TMP_LINK" "$CURRENT_LINK"
SWITCHED=1

if ! run_privileged test -s "$CURRENT_LINK/index.html" || ! run_privileged test -s "$CURRENT_LINK/version.json"; then
    fail "La release active est incomplète."
fi

for asset in "${ASSET_PATHS[@]}"; do
    if ! run_privileged test -s "$CURRENT_LINK/$asset"; then
        fail "Asset déployé manquant : $asset."
    fi
done

run_privileged nginx -t || fail "Configuration Nginx invalide."
if run_privileged systemctl is-active --quiet nginx; then
    run_privileged systemctl reload nginx || fail "Rechargement Nginx impossible."
else
    run_privileged systemctl start nginx || fail "Démarrage Nginx impossible."
fi

DEPLOY_SUCCEEDED=1

# Conserver la release active et les plus récentes ; ne jamais supprimer current.
ACTIVE_RELEASE="$(readlink -f "$CURRENT_LINK")"
mapfile -t RELEASES < <(
    run_privileged find "$RELEASES_DIR" -mindepth 1 -maxdepth 1 -type d ! -name '.staging.*' -printf '%T@ %p\n' \
        | sort -nr | cut -d' ' -f2-
)
KEPT=1
for release in "${RELEASES[@]}"; do
    [[ "$release" == "$ACTIVE_RELEASE" ]] && continue
    if (( KEPT < KEEP_RELEASES )); then
        ((KEPT += 1))
    else
        run_privileged rm -rf -- "$release"
    fi
done

log_success "Frontend déployé : $RELEASE_NAME"
log_info "Release active : $ACTIVE_RELEASE"
log_info "Rechargez le navigateur avec Ctrl + F5."
