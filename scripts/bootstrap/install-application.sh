#!/usr/bin/env bash

# OpenCoach - Installation de l'application.
#
# Responsabilités :
# - créer l'environnement virtuel Python ;
# - installer les dépendances Python ;
# - installer les dépendances frontend ;
# - appliquer les migrations Alembic.
#
# Usage :
#   sudo ./scripts/bootstrap/install-application.sh
#   sudo ./scripts/bootstrap/install-application.sh --dev

set -Eeuo pipefail


SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd -- "$SCRIPT_DIR/../.."
    pwd
)"

# shellcheck disable=SC1091
source "$PROJECT_ROOT/scripts/lib/log.sh"

VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_ALEMBIC="$VENV_DIR/bin/alembic"

PYTHON_CONSTRAINTS_FILE="$PROJECT_ROOT/requirements/constraints.txt"

FRONTEND_DIR="$PROJECT_ROOT/frontend"

ENV_FILE="$PROJECT_ROOT/.env"

DEV_REQUESTED=0


show_help() {
    printf '%s\n' "OpenCoach - Installation applicative"
    printf '\n'
    printf '%s\n' "Utilisation :"
    printf '  %s\n' "$0"
    printf '  %s --dev\n' "$0"
    printf '  %s --help\n' "$0"
}


parse_arguments() {
    while (( $# > 0 )); do
        case "$1" in
            "--dev")
                DEV_REQUESTED=1
                ;;

            "--help"|"-h")
                show_help
                exit 0
                ;;

            *)
                printf 'ERREUR : argument inconnu : %s\n' "$1" >&2
                show_help >&2
                exit 2
                ;;
        esac

        shift
    done
}


require_root() {
    if (( EUID != 0 )); then
        log_error \
            "install-application.sh doit être exécuté avec sudo."

        exit 1
    fi
}


resolve_project_owner() {
    OPENCOACH_USER="$(
        stat -c '%U' "$PROJECT_ROOT"
    )"

    OPENCOACH_GROUP="$(
        stat -c '%G' "$PROJECT_ROOT"
    )"

    if [[ "$OPENCOACH_USER" == "root" ]]; then
        log_error \
            "Le projet OpenCoach ne doit pas appartenir à root."

        exit 1
    fi
}


run_as_project_owner() {
    runuser \
        -u "$OPENCOACH_USER" \
        -- \
        "$@"
}


create_virtual_environment() {
    if [[ -x "$VENV_PYTHON" ]]; then
        log_success \
            "Environnement virtuel Python déjà présent."

        return
    fi

    log_info \
        "Création de l'environnement virtuel Python"

    run_as_project_owner \
        python3 \
        -m venv \
        "$VENV_DIR"

    if [[ ! -x "$VENV_PYTHON" ]]; then
        log_error \
            "Création de l'environnement virtuel impossible."

        return 1
    fi

    log_success \
        "Environnement virtuel Python créé."
}


install_python_application() {
    local install_target="."

    if (( DEV_REQUESTED == 1 )); then
        install_target=".[dev]"
    fi

    if [[ ! -f "$PYTHON_CONSTRAINTS_FILE" ]]; then
        log_error \
            "Le fichier requirements/constraints.txt est introuvable."

        return 1
    fi

    log_info \
        "Utilisation des dépendances Python verrouillées"

    log_info \
        "Mise à jour de pip"

    run_as_project_owner \
        env \
        PIP_CONSTRAINT="$PYTHON_CONSTRAINTS_FILE" \
        PIP_BUILD_CONSTRAINT="$PYTHON_CONSTRAINTS_FILE" \
        "$VENV_PYTHON" \
        -m pip \
        install \
        --upgrade \
        pip

    log_info \
        "Installation d'OpenCoach : $install_target"

    (
        cd "$PROJECT_ROOT"

        run_as_project_owner \
            env \
            PIP_CONSTRAINT="$PYTHON_CONSTRAINTS_FILE" \
            PIP_BUILD_CONSTRAINT="$PYTHON_CONSTRAINTS_FILE" \
            "$VENV_PYTHON" \
            -m pip \
            install \
            -e \
            "$install_target"
    )

    log_info \
        "Vérification des dépendances Python"

    run_as_project_owner \
        "$VENV_PYTHON" \
        -m pip \
        check

    log_success \
        "Dépendances Python verrouillées installées et validées."
}


configure_authentication() {
    local auth_keys=(
        "OPENCOACH_AUTH_PIN_SALT"
        "OPENCOACH_AUTH_PIN_HASH"
        "OPENCOACH_AUTH_SESSION_SECRET"
    )

    local configured_count=0
    local key

    if [[ -f "$ENV_FILE" ]]; then
        for key in "${auth_keys[@]}"; do
            if grep -qE \
                "^${key}=.+" \
                "$ENV_FILE"; then

                configured_count=$((configured_count + 1))
            fi
        done
    fi

    if (( configured_count == ${#auth_keys[@]} )); then
        log_success \
            "Authentification OpenCoach déjà configurée."

        return
    fi

    if (( configured_count > 0 )); then
        log_error \
            "Configuration d'authentification OpenCoach incomplète dans .env."

        log_error \
            "L'installation refuse de remplacer des secrets existants."

        return 1
    fi

    log_info \
        "Configuration de l'accès sécurisé à OpenCoach"

    printf '\n'
    printf '%s\n' \
        "Un code PIN personnel à 6 chiffres est requis."
    printf '%s\n' \
        "Ce code permettra de se connecter à OpenCoach."
    printf '\n'

    local pin=""
    local pin_confirmation=""

    while true; do
        read -r -s \
            -p "Code PIN OpenCoach (6 chiffres) : " \
            pin

        printf '\n'

        if [[ ! "$pin" =~ ^[0-9]{6}$ ]]; then
            log_warning \
                "Le code PIN doit contenir exactement 6 chiffres."

            continue
        fi

        read -r -s \
            -p "Confirmez le code PIN : " \
            pin_confirmation

        printf '\n'

        if [[ "$pin" != "$pin_confirmation" ]]; then
            log_warning \
                "Les deux codes PIN ne correspondent pas."

            continue
        fi

        break
    done

    touch "$ENV_FILE"

    chown \
        "$OPENCOACH_USER:$OPENCOACH_GROUP" \
        "$ENV_FILE"

    chmod \
        600 \
        "$ENV_FILE"

    if ! run_as_project_owner \
        env \
        OPENCOACH_INSTALL_PIN="$pin" \
        "$VENV_PYTHON" \
        - "$ENV_FILE" <<'PYTHON'
import base64
import hashlib
import os
import secrets
import sys

from pathlib import Path


env_path = Path(
    sys.argv[1]
)

pin = os.environ.get(
    "OPENCOACH_INSTALL_PIN",
    "",
)

if (
    len(pin) != 6
    or not pin.isdigit()
):
    raise SystemExit(
        "PIN invalide."
    )


salt = secrets.token_bytes(
    16
)

pin_hash = hashlib.scrypt(
    pin.encode(
        "utf-8"
    ),
    salt=salt,
    n=2**15,
    r=8,
    p=1,
    dklen=32,
    maxmem=64 * 1024 * 1024,
)


values = {
    "OPENCOACH_AUTH_PIN_SALT": (
        base64
        .urlsafe_b64encode(
            salt
        )
        .decode(
            "ascii"
        )
    ),
    "OPENCOACH_AUTH_PIN_HASH": (
        base64
        .urlsafe_b64encode(
            pin_hash
        )
        .decode(
            "ascii"
        )
    ),
    "OPENCOACH_AUTH_SESSION_SECRET": (
        secrets.token_urlsafe(
            48
        )
    ),
    "OPENCOACH_AUTH_SESSION_DAYS": "30",
    "OPENCOACH_AUTH_MAX_ATTEMPTS": "5",
    "OPENCOACH_AUTH_LOCK_SECONDS": "300",
}


lines = []

if env_path.exists():
    lines = env_path.read_text(
        encoding="utf-8",
    ).splitlines()


managed_keys = set(
    values
)

filtered_lines = [
    line
    for line in lines
    if not any(
        line.startswith(
            key + "="
        )
        for key in managed_keys
    )
]


while (
    filtered_lines
    and filtered_lines[-1] == ""
):
    filtered_lines.pop()


if filtered_lines:
    filtered_lines.append(
        ""
    )


filtered_lines.append(
    "# OpenCoach authentication"
)


for key, value in values.items():
    filtered_lines.append(
        f"{key}={value}"
    )


env_path.write_text(
    "\n".join(
        filtered_lines
    )
    + "\n",
    encoding="utf-8",
)
PYTHON
    then
        unset pin
        unset pin_confirmation

        log_error \
            "Impossible de générer les secrets d'authentification."

        return 1
    fi

    unset pin
    unset pin_confirmation

    chmod \
        600 \
        "$ENV_FILE"

    chown \
        "$OPENCOACH_USER:$OPENCOACH_GROUP" \
        "$ENV_FILE"

    log_success \
        "Authentification OpenCoach configurée."

    log_info \
        "Le PIN n'est pas stocké en clair."
}



configure_web_push() {
    local vapid_keys=(
        "OPENCOACH_VAPID_PRIVATE_KEY"
        "OPENCOACH_VAPID_PUBLIC_KEY"
        "OPENCOACH_VAPID_SUBJECT"
    )

    local configured_count=0
    local key

    for key in "${vapid_keys[@]}"; do
        if [[ -f "$ENV_FILE" ]] \
            && grep -qE \
                "^${key}=.+" \
                "$ENV_FILE"; then

            configured_count=$((configured_count + 1))
        fi
    done


    if ((
        configured_count
        == ${#vapid_keys[@]}
    )); then
        log_success \
            "Web Push VAPID déjà configuré."

        return 0
    fi


    if (( configured_count > 0 )); then
        log_error \
            "Configuration Web Push VAPID incomplète dans $ENV_FILE."

        log_error \
            "Les clés existantes ne seront pas remplacées."

        return 1
    fi


    log_info \
        "Génération automatique des clés Web Push VAPID"


    touch \
        "$ENV_FILE"

    chown \
        "$OPENCOACH_USER:$OPENCOACH_GROUP" \
        "$ENV_FILE"

    chmod \
        600 \
        "$ENV_FILE"


    if ! run_as_project_owner \
        "$VENV_PYTHON" \
        - "$ENV_FILE" <<'PYTHON'
import base64
import sys

from pathlib import Path

from cryptography.hazmat.primitives import (
    serialization,
)
from cryptography.hazmat.primitives.asymmetric import (
    ec,
)


env_path = Path(
    sys.argv[1]
)


private_key = ec.generate_private_key(
    ec.SECP256R1()
)


private_der = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=(
        serialization.NoEncryption()
    ),
)


private_value = (
    base64
    .urlsafe_b64encode(
        private_der
    )
    .decode(
        "ascii"
    )
    .rstrip(
        "="
    )
)


public_raw = (
    private_key
    .public_key()
    .public_bytes(
        encoding=serialization.Encoding.X962,
        format=(
            serialization
            .PublicFormat
            .UncompressedPoint
        ),
    )
)


public_value = (
    base64
    .urlsafe_b64encode(
        public_raw
    )
    .decode(
        "ascii"
    )
    .rstrip(
        "="
    )
)


if len(public_raw) != 65:
    raise SystemExit(
        "Clé publique VAPID invalide."
    )


values = {
    "OPENCOACH_VAPID_PRIVATE_KEY":
        private_value,

    "OPENCOACH_VAPID_PUBLIC_KEY":
        public_value,

    "OPENCOACH_VAPID_SUBJECT":
        "mailto:admin@opencoach.local",
}


existing_lines = []

if env_path.exists():
    existing_lines = (
        env_path
        .read_text(
            encoding="utf-8",
        )
        .splitlines()
    )


managed_keys = set(
    values
)


lines = [
    line
    for line in existing_lines
    if not any(
        line.startswith(
            f"{key}="
        )
        for key in managed_keys
    )
]


while (
    lines
    and not lines[-1].strip()
):
    lines.pop()


if lines:
    lines.append(
        ""
    )


lines.append(
    "# OpenCoach Web Push VAPID"
)


for key, value in values.items():
    lines.append(
        f"{key}={value}"
    )


env_path.write_text(
    "\n".join(
        lines
    )
    + "\n",
    encoding="utf-8",
)


print(
    "Clés VAPID générées."
)
PYTHON
    then
        log_error \
            "Impossible de générer les clés VAPID."

        return 1
    fi


    chmod \
        600 \
        "$ENV_FILE"

    chown \
        "$OPENCOACH_USER:$OPENCOACH_GROUP" \
        "$ENV_FILE"


    log_success \
        "Web Push VAPID configuré automatiquement."

    return 0
}


install_frontend_application() {
    if [[ ! -f "$FRONTEND_DIR/package-lock.json" ]]; then
        log_error \
            "frontend/package-lock.json est introuvable."

        return 1
    fi

    log_info \
        "Installation des dépendances frontend"

    (
        cd "$FRONTEND_DIR"

        run_as_project_owner \
            npm ci

        log_info \
            "Construction du frontend OpenCoach"

        run_as_project_owner \
            npm run build
    )

    if [[ ! -f "$FRONTEND_DIR/dist/index.html" ]]; then
        log_error \
            "La construction du frontend n'a pas produit dist/index.html."

        return 1
    fi

    log_success \
        "Dépendances frontend installées et frontend construit."
}

apply_database_migrations() {
    if [[ ! -x "$VENV_ALEMBIC" ]]; then
        log_error \
            "Alembic est introuvable dans l'environnement virtuel."

        return 1
    fi

    log_info \
        "Application des migrations Alembic"

    (
        cd "$PROJECT_ROOT"

        run_as_project_owner \
            "$VENV_ALEMBIC" \
            upgrade \
            head
    )

    log_success \
        "Base de données à jour."
}


main() {
    parse_arguments "$@"

    require_root
    resolve_project_owner

    log_info \
        "Installation applicative OpenCoach"

    create_virtual_environment

    install_python_application

    configure_authentication

    configure_web_push

    install_frontend_application

    apply_database_migrations

    log_success \
        "Installation applicative OpenCoach terminée."
}


main "$@"
