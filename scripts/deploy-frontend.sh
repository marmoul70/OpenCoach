#!/usr/bin/env bash

# OpenCoach - Déploiement frontend par releases atomiques.
#
# Usage :
#   ./scripts/deploy-frontend.sh
#
# Le build et les contrôles sont exécutés sans privilèges. Seules les
# opérations dans WEB_ROOT et le rechargement Nginx utilisent sudo.
# En cas d'échec après bascule, la release précédente est restaurée.

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DIST_DIR="$FRONTEND_DIR/dist"
WEB_ROOT="${OPENCOACH_WEB_ROOT:-/var/www/opencoach}"
RELEASES_DIR="$WEB_ROOT/releases"
CURRENT_LINK="$WEB_ROOT/current"
KEEP_RELEASES=5
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

rollback_current() {
    local previous_target="$1"
    local rollback_link="$WEB_ROOT/.current-rollback"

    if [[ -n "$previous_target" ]]; then
        sudo ln -sfn "$previous_target" "$rollback_link"
        sudo mv -Tf "$rollback_link" "$CURRENT_LINK"
    else
        sudo rm -f "$CURRENT_LINK"
    fi

    if sudo nginx -t; then
        sudo systemctl reload nginx || true
    fi
}

cleanup() {
    local status=$?
    trap - EXIT
    if [[ -n "$STAGING_DIR" ]]; then
        sudo rm -rf -- "$STAGING_DIR" || true
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
command -v sudo >/dev/null 2>&1 || fail "sudo est requis."
[[ "$WEB_ROOT" == /* ]] || fail "OPENCOACH_WEB_ROOT doit être un chemin absolu."
[[ -f "$PROJECT_ROOT/VERSION" ]] || fail "Fichier VERSION introuvable."
[[ -f "$FRONTEND_DIR/package.json" ]] || fail "Projet frontend introuvable."
[[ -f "$FRONTEND_DIR/package-lock.json" ]] || fail "package-lock.json introuvable."

VERSION="$(tr -d '[:space:]' < "$PROJECT_ROOT/VERSION")"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9.-]+)?$ ]] || fail "Version applicative invalide : $VERSION"

if [[ -n "$(git -C "$PROJECT_ROOT" status --porcelain)" ]]; then
    log_error "Le dépôt Git contient des modifications non validées."
    git -C "$PROJECT_ROOT" status --short
    fail "Committez ou annulez les modifications avant le déploiement."
fi

GIT_SHA="$(git -C "$PROJECT_ROOT" rev-parse --short=7 HEAD)"
RELEASE_NAME="${VERSION}-${GIT_SHA}"
RELEASE_DIR="$RELEASES_DIR/$RELEASE_NAME"

log_info "Version : $VERSION"
log_info "Commit : $GIT_SHA"
log_info "Cible : $WEB_ROOT"

log_info "Installation déterministe des dépendances frontend..."
(
    cd "$FRONTEND_DIR"
    npm ci
    npm run lint
    npm run build
) || fail "Installation, lint ou compilation frontend en échec. Aucun déploiement effectué."

[[ -s "$DIST_DIR/index.html" ]] || fail "Build invalide : index.html absent."
[[ -d "$DIST_DIR/assets" ]] || fail "Build invalide : dossier assets absent."

mapfile -t ASSET_PATHS < <(
    grep -oE 'assets/[^"]+\.(js|css)' "$DIST_DIR/index.html" | sort -u
)
(("${#ASSET_PATHS[@]}" > 0)) || fail "Aucun fichier JS/CSS référencé dans index.html."

for asset in "${ASSET_PATHS[@]}"; do
    [[ -s "$DIST_DIR/$asset" ]] || fail "Asset compilé manquant : $asset"
done

BUILD_TIME="$(date --utc '+%Y-%m-%dT%H:%M:%SZ')"
cat > "$DIST_DIR/version.json" <<JSON
{
  "application": "OpenCoach",
  "version": "$VERSION",
  "commit": "$GIT_SHA",
  "built_at": "$BUILD_TIME"
}
JSON

log_success "Build et assets validés."
sudo -v
sudo install -d -m 755 "$RELEASES_DIR"

if [[ -e "$CURRENT_LINK" && ! -L "$CURRENT_LINK" ]]; then
    fail "$CURRENT_LINK existe mais n'est pas un lien symbolique. Déploiement annulé."
fi

if [[ -L "$CURRENT_LINK" ]]; then
    PREVIOUS_TARGET="$(readlink "$CURRENT_LINK")"
fi

if [[ ! -d "$RELEASE_DIR" ]]; then
    STAGING_DIR="$(sudo mktemp -d "$RELEASES_DIR/.staging.XXXXXX")"
    sudo cp -a "$DIST_DIR/." "$STAGING_DIR/"
    sudo test -s "$STAGING_DIR/index.html" || fail "index.html absent de la release temporaire."
    sudo test -s "$STAGING_DIR/version.json" || fail "version.json absent de la release temporaire."
    sudo mv "$STAGING_DIR" "$RELEASE_DIR"
    STAGING_DIR=""
else
    log_info "Release déjà présente : réutilisation de $RELEASE_NAME"
fi

TMP_LINK="$WEB_ROOT/.current-new"
sudo rm -f "$TMP_LINK"
sudo ln -s "releases/$RELEASE_NAME" "$TMP_LINK"
sudo mv -Tf "$TMP_LINK" "$CURRENT_LINK"
SWITCHED=1

if ! sudo test -s "$CURRENT_LINK/index.html" || ! sudo test -s "$CURRENT_LINK/version.json"; then
    fail "La release active est incomplète."
fi

for asset in "${ASSET_PATHS[@]}"; do
    if ! sudo test -s "$CURRENT_LINK/$asset"; then
        fail "Asset déployé manquant : $asset."
    fi
done

if ! sudo nginx -t; then
    fail "Configuration Nginx invalide."
fi

if ! sudo systemctl reload nginx; then
    fail "Rechargement Nginx impossible."
fi

DEPLOY_SUCCEEDED=1

# Conserver la release active et les plus récentes ; ne jamais supprimer current.
ACTIVE_RELEASE="$(readlink -f "$CURRENT_LINK")"
mapfile -t RELEASES < <(
    sudo find "$RELEASES_DIR" -mindepth 1 -maxdepth 1 -type d ! -name '.staging.*' -printf '%T@ %p\n' \
        | sort -nr | cut -d' ' -f2-
)
KEPT=1
for release in "${RELEASES[@]}"; do
    [[ "$release" == "$ACTIVE_RELEASE" ]] && continue
    if (( KEPT < KEEP_RELEASES )); then
        ((KEPT += 1))
    else
        sudo rm -rf -- "$release"
    fi
done

log_success "Frontend déployé : $RELEASE_NAME"
log_info "Release active : $ACTIVE_RELEASE"
log_info "Rechargez le navigateur avec Ctrl + F5."
