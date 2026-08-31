#!/usr/bin/env bash

set -Eeuo pipefail


WEB_ROOT="/var/www/opencoach"
RELEASES_DIR="$WEB_ROOT/releases"
CURRENT_LINK="$WEB_ROOT/current"


echo "============================================================"
echo " OpenCoach - Rollback frontend"
echo "============================================================"
echo


if [[ ! -d "$RELEASES_DIR" ]]; then
    echo "ERREUR : dossier releases absent :" >&2
    echo "$RELEASES_DIR" >&2
    exit 1
fi


if [[ ! -L "$CURRENT_LINK" ]]; then
    echo "ERREUR : current n'est pas un lien symbolique." >&2
    exit 1
fi


CURRENT_RELEASE="$(
    readlink -f \
        "$CURRENT_LINK"
)"


echo "Release actuelle :"
echo "$CURRENT_RELEASE"
echo


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


CANDIDATES=()

for release in "${RELEASES[@]}"; do
    release_real="$(
        readlink -f \
            "$release"
    )"

    if [[ "$release_real" != "$CURRENT_RELEASE" ]]; then
        CANDIDATES+=(
            "$release_real"
        )
    fi
done


if (( ${#CANDIDATES[@]} == 0 )); then
    echo "ERREUR : aucune autre release disponible." >&2
    exit 1
fi


if [[ $# -gt 0 ]]; then
    REQUESTED="$1"

    if [[ "$REQUESTED" == /* ]]; then
        TARGET="$REQUESTED"
    else
        TARGET="$RELEASES_DIR/$REQUESTED"
    fi

    TARGET="$(
        readlink -f \
            "$TARGET"
    )"

    VALID=false

    for release in "${CANDIDATES[@]}"; do
        if [[ "$release" == "$TARGET" ]]; then
            VALID=true
            break
        fi
    done

    if [[ "$VALID" != true ]]; then
        echo "ERREUR : release demandée invalide :" >&2
        echo "$REQUESTED" >&2
        echo
        echo "Releases disponibles :" >&2

        for release in "${CANDIDATES[@]}"; do
            basename "$release" >&2
        done

        exit 1
    fi
else
    TARGET="${CANDIDATES[0]}"
fi


if [[ ! -f "$TARGET/index.html" ]]; then
    echo "ERREUR : index.html absent dans :" >&2
    echo "$TARGET" >&2
    exit 1
fi


if [[ ! -f "$TARGET/version.json" ]]; then
    echo "ERREUR : version.json absent dans :" >&2
    echo "$TARGET" >&2
    exit 1
fi


echo "Rollback vers :"
echo "$TARGET"
echo


echo "Version cible :"

python -m json.tool \
    "$TARGET/version.json"

echo


TMP_LINK="$WEB_ROOT/.current-rollback"


sudo rm -f \
    "$TMP_LINK"


sudo ln -s \
    "releases/$(basename "$TARGET")" \
    "$TMP_LINK"


sudo mv -Tf \
    "$TMP_LINK" \
    "$CURRENT_LINK"


echo "Validation Nginx..."

if ! sudo nginx -t; then
    echo
    echo "ERREUR : configuration Nginx invalide." >&2
    echo "Restauration du lien précédent..." >&2

    sudo rm -f \
        "$TMP_LINK"

    sudo ln -s \
        "releases/$(basename "$CURRENT_RELEASE")" \
        "$TMP_LINK"

    sudo mv -Tf \
        "$TMP_LINK" \
        "$CURRENT_LINK"

    exit 1
fi


sudo systemctl reload nginx


echo
echo "============================================================"
echo " ROLLBACK TERMINE"
echo "============================================================"
echo

echo "Release active :"

readlink -f \
    "$CURRENT_LINK"

echo

echo "Version active :"

python -m json.tool \
    "$CURRENT_LINK/version.json"
