#!/usr/bin/env bash

set -Eeuo pipefail


PROJECT_ROOT="$HOME/Projects/OpenCoach"

FRONTEND_DIR="$PROJECT_ROOT/frontend"

WEB_ROOT="/var/www/opencoach"

RELEASES_DIR="$WEB_ROOT/releases"

CURRENT_LINK="$WEB_ROOT/current"

KEEP_RELEASES=5


cd "$PROJECT_ROOT"


echo "============================================================"
echo " OpenCoach - Déploiement frontend"
echo "============================================================"
echo


# ============================================================
# VERSION
# ============================================================

if [[ ! -f VERSION ]]; then
    echo "ERREUR : fichier VERSION absent." >&2
    exit 1
fi


VERSION="$(
    tr -d '[:space:]' \
        < VERSION
)"


if [[ -z "$VERSION" ]]; then
    echo "ERREUR : VERSION vide." >&2
    exit 1
fi


GIT_SHA="$(
    git rev-parse \
        --short=7 \
        HEAD
)"


RELEASE_NAME="${VERSION}-${GIT_SHA}"

RELEASE_DIR="$RELEASES_DIR/$RELEASE_NAME"


echo "Version : $VERSION"
echo "Commit  : $GIT_SHA"
echo "Release : $RELEASE_NAME"
echo


# ============================================================
# ETAT GIT
# ============================================================

if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERREUR : le dépôt Git n'est pas propre." >&2
    echo
    git status --short
    echo
    echo "Commit ou annule les modifications avant déploiement."
    exit 1
fi


# ============================================================
# BUILD
# ============================================================

echo "============================================================"
echo " Build frontend"
echo "============================================================"

cd "$FRONTEND_DIR"

npm run build


echo
echo "============================================================"
echo " Lint frontend"
echo "============================================================"

npm run lint


# ============================================================
# METADONNEES BUILD
# ============================================================

BUILD_TIME="$(
    date \
        --utc \
        '+%Y-%m-%dT%H:%M:%SZ'
)"


cat > "$FRONTEND_DIR/dist/version.json" <<JSON
{
  "application": "OpenCoach",
  "version": "$VERSION",
  "commit": "$GIT_SHA",
  "built_at": "$BUILD_TIME"
}
JSON


# ============================================================
# PREPARATION NGINX
# ============================================================

echo
echo "============================================================"
echo " Création release"
echo "============================================================"


sudo mkdir -p \
    "$RELEASES_DIR"


if [[ -e "$RELEASE_DIR" ]]; then
    echo "La release existe déjà :"
    echo "$RELEASE_DIR"
    echo
    echo "Bascule vers cette release."
else
    TMP_RELEASE="${RELEASE_DIR}.tmp"

    sudo rm -rf \
        "$TMP_RELEASE"

    sudo mkdir -p \
        "$TMP_RELEASE"

    sudo cp -a \
        "$FRONTEND_DIR/dist/." \
        "$TMP_RELEASE/"

    sudo mv \
        "$TMP_RELEASE" \
        "$RELEASE_DIR"
fi


# ============================================================
# BASCULE ATOMIQUE
# ============================================================

echo
echo "============================================================"
echo " Bascule current"
echo "============================================================"


TMP_LINK="$WEB_ROOT/.current-new"


sudo rm -f \
    "$TMP_LINK"


sudo ln -s \
    "releases/$RELEASE_NAME" \
    "$TMP_LINK"


sudo mv -Tf \
    "$TMP_LINK" \
    "$CURRENT_LINK"


echo "current -> releases/$RELEASE_NAME"


# ============================================================
# TEST
# ============================================================

echo
echo "============================================================"
echo " Validation release"
echo "============================================================"


if [[ ! -f "$CURRENT_LINK/index.html" ]]; then
    echo "ERREUR : index.html absent dans current." >&2
    exit 1
fi


if [[ ! -f "$CURRENT_LINK/version.json" ]]; then
    echo "ERREUR : version.json absent." >&2
    exit 1
fi


sudo nginx -t


# ============================================================
# RELOAD
# ============================================================

sudo systemctl reload nginx


# ============================================================
# RETENTION
# ============================================================

echo
echo "============================================================"
echo " Nettoyage anciennes releases"
echo "============================================================"


mapfile -t RELEASES < <(
    sudo find \
        "$RELEASES_DIR" \
        -mindepth 1 \
        -maxdepth 1 \
        -type d \
        -printf '%T@ %p\n' \
        | sort -nr \
        | awk '{print $2}'
)


if (( ${#RELEASES[@]} > KEEP_RELEASES )); then
    for old_release in "${RELEASES[@]:$KEEP_RELEASES}"; do
        echo "Suppression : $old_release"

        sudo rm -rf \
            "$old_release"
    done
else
    echo "Aucune ancienne release à supprimer."
fi


# ============================================================
# RESULTAT
# ============================================================

echo
echo "============================================================"
echo " DEPLOIEMENT TERMINE"
echo "============================================================"
echo
echo "Version : $VERSION"
echo "Commit  : $GIT_SHA"
echo
echo "Release active :"
readlink -f \
    "$CURRENT_LINK"
echo
