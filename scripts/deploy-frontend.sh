#!/usr/bin/env bash

# OpenCoach - Build and deploy the production frontend to Nginx.
#
# Usage:
#   ./scripts/deploy-frontend.sh
#
# The frontend is built as the current user. Only the copy to the Nginx
# document root and the Nginx reload require sudo.

set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DIST_DIR="$FRONTEND_DIR/dist"
WEB_ROOT="/var/www/opencoach"

log() {
    printf '[%s] %s\n' "$1" "$2"
}

fail() {
    log "ERREUR" "$1" >&2
    exit 1
}

command -v node >/dev/null 2>&1 || fail "Node.js est requis."
command -v npm >/dev/null 2>&1 || fail "npm est requis."
command -v sudo >/dev/null 2>&1 || fail "sudo est requis."

[[ -f "$FRONTEND_DIR/package.json" ]] || fail "Projet frontend introuvable : $FRONTEND_DIR"
[[ -f "$FRONTEND_DIR/package-lock.json" ]] || fail "package-lock.json introuvable."

log "INFO" "Compilation du frontend..."
(
    cd "$FRONTEND_DIR"
    npm run build
) || fail "La compilation a échoué. Aucun déploiement effectué."

[[ -s "$DIST_DIR/index.html" ]] || fail "Build invalide : index.html absent."
[[ -d "$DIST_DIR/assets" ]] || fail "Build invalide : dossier assets absent."

# Vérifie que les fichiers JS/CSS référencés par index.html existent dans dist.
mapfile -t ASSET_PATHS < <(
    grep -oE 'assets/[^"]+\.(js|css)' "$DIST_DIR/index.html" | sort -u
)

(("${#ASSET_PATHS[@]}" > 0)) || fail "Aucun fichier JS/CSS référencé dans index.html."

for asset in "${ASSET_PATHS[@]}"; do
    [[ -s "$DIST_DIR/$asset" ]] || fail "Fichier compilé manquant : $DIST_DIR/$asset"
done

log "INFO" "Validation du build réussie."
log "INFO" "Préparation des droits administrateur..."
sudo -v

sudo install -d "$WEB_ROOT"
sudo cp -a "$DIST_DIR/." "$WEB_ROOT/" || fail "Copie vers $WEB_ROOT impossible."

# Vérifie que Nginx sert bien le même index que le build fraîchement produit.
cmp -s "$DIST_DIR/index.html" "$WEB_ROOT/index.html" \
    || fail "Le index.html déployé ne correspond pas au build."

for asset in "${ASSET_PATHS[@]}"; do
    sudo test -s "$WEB_ROOT/$asset" \
        || fail "Fichier déployé manquant : $WEB_ROOT/$asset"
done

if command -v nginx >/dev/null 2>&1 && systemctl is-active --quiet nginx; then
    sudo nginx -t || fail "Configuration Nginx invalide. Le rechargement est annulé."
    sudo systemctl reload nginx || fail "Impossible de recharger Nginx."
    log "OK" "Nginx rechargé."
else
    log "ATTENTION" "Nginx n'est pas actif : les fichiers sont copiés, mais aucun rechargement n'a été effectué."
fi

log "OK" "Frontend déployé dans $WEB_ROOT."
log "INFO" "Rechargez le navigateur avec Ctrl + F5."
