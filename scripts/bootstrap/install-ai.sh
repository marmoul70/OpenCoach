#!/usr/bin/env bash

# OpenCoach - Installation du moteur IA local Ollama.
#
# Cette installation est optionnelle. Le backend et la planification
# OpenCoach ne dépendent jamais du service Ollama.
#
# Usage :
#   sudo ./scripts/bootstrap/install-ai.sh

set -Eeuo pipefail

SCRIPT_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd -- "$SCRIPT_DIR/../.."
    pwd
)"

# shellcheck source=../lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

ENV_FILE="$PROJECT_ROOT/.env"
OLLAMA_INSTALL_URL="https://ollama.com/install.sh"
DEFAULT_MODEL="phi4-mini:latest"
OLLAMA_API_URL="http://127.0.0.1:11434/api/version"


show_help() {
    cat <<'HELP'
OpenCoach - Installation du moteur IA local

Utilisation :
  sudo ./scripts/bootstrap/install-ai.sh
  sudo ./scripts/bootstrap/install-ai.sh --help

Ce script installe ou réutilise Ollama, active son service local
et vérifie la présence du modèle configuré dans .env.

L'IA reste désactivée dans OpenCoach jusqu'à activation explicite
de OPENCOACH_AI_ENABLED après intégration du backend.
HELP
}


parse_arguments() {
    while (( $# > 0 )); do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Argument inconnu : $1"
                show_help >&2
                exit 2
                ;;
        esac
    done
}


require_root() {
    if (( EUID != 0 )); then
        log_error "install-ai.sh doit être exécuté avec sudo."
        exit 1
    fi
}


ensure_environment_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env est introuvable. Exécutez d'abord install.sh."
        return 1
    fi

    if ! python3 - "$ENV_FILE" "$DEFAULT_MODEL" <<'PYTHON'
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

env_path = Path(sys.argv[1])
default_model = sys.argv[2]

defaults = {
    "OPENCOACH_AI_ENABLED": "false",
    "OPENCOACH_AI_PROVIDER": "ollama",
    "OPENCOACH_AI_BASE_URL": "http://127.0.0.1:11434",
    "OPENCOACH_AI_MODEL": default_model,
    "OPENCOACH_AI_CONNECT_TIMEOUT_SECONDS": "2",
    "OPENCOACH_AI_READ_TIMEOUT_SECONDS": "90",
    "OPENCOACH_AI_MAX_CONCURRENCY": "1",
}

if env_path.is_symlink():
    raise SystemExit("Refus de modifier un fichier .env symbolique.")

try:
    original_stat = env_path.stat()
    original = env_path.read_text(encoding="utf-8")
except OSError as exc:
    raise SystemExit(f"Lecture du fichier .env impossible : {exc}")

lines = original.splitlines()
seen = set()
duplicates = set()
updated = []

assignment = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")

# Première passe : détecter les doublons avant toute modification.
for line in lines:
    if line.lstrip().startswith("#"):
        continue

    match = assignment.match(line)
    if not match:
        continue

    key = match.group(1)
    if key in defaults:
        if key in seen:
            duplicates.add(key)
        seen.add(key)

if duplicates:
    names = ", ".join(sorted(duplicates))
    raise SystemExit(
        f"Variables IA déclarées plusieurs fois dans .env : {names}. "
        "Corrigez les doublons avant de relancer l'installation."
    )

# Deuxième passe : conserver les lignes et valeurs existantes.
seen.clear()

for line in lines:
    if line.lstrip().startswith("#"):
        updated.append(line)
        continue

    match = assignment.match(line)
    if not match:
        updated.append(line)
        continue

    key = match.group(1)
    if key not in defaults:
        updated.append(line)
        continue

    seen.add(key)
    current = line.split("=", 1)[1].strip()

    # Une valeur vide ou composée uniquement de guillemets
    # reçoit la valeur par défaut. Toute valeur non vide est conservée.
    if current.strip("'\""):
        updated.append(line)
    else:
        updated.append(f"{key}={defaults[key]}")

missing = {
    key: value
    for key, value in defaults.items()
    if key not in seen
}

if missing:
    if updated and updated[-1].strip():
        updated.append("")

    updated.append("# OpenCoach - IA locale (désactivée jusqu'à validation)")
    updated.extend(f"{key}={value}" for key, value in missing.items())

result = "\n".join(updated) + "\n"

if result == original and stat.S_IMODE(original_stat.st_mode) == 0o600:
    raise SystemExit(0)

temp_path = None

try:
    fd, temp_name = tempfile.mkstemp(
        prefix=".env.",
        suffix=".tmp",
        dir=str(env_path.parent),
    )
    temp_path = Path(temp_name)

    with os.fdopen(fd, "w", encoding="utf-8") as temporary:
        temporary.write(result)
        temporary.flush()
        os.fsync(temporary.fileno())

    os.chown(temp_path, original_stat.st_uid, original_stat.st_gid)
    os.chmod(temp_path, 0o600)
    os.replace(temp_path, env_path)

    directory_fd = os.open(env_path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)

except Exception:
    if temp_path is not None:
        temp_path.unlink(missing_ok=True)
    raise
PYTHON
    then
        log_error "Impossible de préparer les paramètres IA dans .env."
        return 1
    fi

    chmod 600 "$ENV_FILE"
}


read_configured_model() {
    local configured_model

    configured_model="$(
        awk -F= '
            $1 == "OPENCOACH_AI_MODEL" {
                sub(/^[^=]*=/, "")
                gsub(/^[[:space:]\047"]+|[[:space:]\047"]+$/, "")
                value = $0
            }
            END { print value }
        ' "$ENV_FILE"
    )"

    if [[ -z "$configured_model" ]]; then
        configured_model="$DEFAULT_MODEL"
    fi

    if [[ ! "$configured_model" =~ ^[A-Za-z0-9._:-]+$ ]]; then
        log_error "OPENCOACH_AI_MODEL contient un nom de modèle invalide."
        return 1
    fi

    printf '%s' "$configured_model"
}


install_ollama_if_missing() {
    if command -v ollama >/dev/null 2>&1; then
        log_success "Ollama est déjà installé : $(ollama --version)"
        return 0
    fi

    local installer_file
    installer_file="$(mktemp)"

    log_info "Téléchargement de l'installateur officiel Ollama"

    if ! curl --fail --location --silent --show-error \
        "$OLLAMA_INSTALL_URL" --output "$installer_file"; then
        rm -f "$installer_file"
        log_error "Téléchargement de l'installateur Ollama impossible."
        return 1
    fi

    if [[ ! -s "$installer_file" ]]; then
        rm -f "$installer_file"
        log_error "L'installateur Ollama téléchargé est vide."
        return 1
    fi

    log_info "Installation d'Ollama depuis l'installateur officiel"

    if ! bash "$installer_file"; then
        rm -f "$installer_file"
        log_error "L'installateur officiel Ollama a échoué."
        return 1
    fi

    rm -f "$installer_file"

    if ! command -v ollama >/dev/null 2>&1; then
        log_error "Ollama reste introuvable après son installation."
        return 1
    fi

    log_success "Ollama installé : $(ollama --version)"
}


start_ollama_service() {
    if ! systemctl enable --now ollama.service; then
        log_error "Impossible d'activer le service ollama.service."
        return 1
    fi

    if ! systemctl is-active --quiet ollama.service; then
        log_error "Le service Ollama n'est pas actif."
        return 1
    fi

    local attempt

    for ((attempt = 1; attempt <= 30; attempt++)); do
        if curl --fail --silent "$OLLAMA_API_URL" >/dev/null 2>&1; then
            log_success "API Ollama disponible sur 127.0.0.1:11434."
            return 0
        fi

        sleep 1
    done

    log_error "L'API Ollama n'est pas disponible après 30 secondes."
    return 1
}


ensure_model_available() {
    local model="$1"

    if ollama list | awk 'NR > 1 { print $1 }' | grep -Fxq "$model"; then
        log_success "Modèle IA déjà installé : $model"
        return 0
    fi

    log_info "Téléchargement du modèle IA : $model"

    ollama pull "$model"

    if ! ollama list | awk 'NR > 1 { print $1 }' | grep -Fxq "$model"; then
        log_error "Le modèle $model n'apparaît pas dans ollama list."
        return 1
    fi

    log_success "Modèle IA installé : $model"
}


main() {
    parse_arguments "$@"
    require_root

    log_info "Préparation du moteur IA local OpenCoach"

    ensure_environment_file

    # Valider la configuration avant toute opération sur le système.
        # Valider la configuration avant toute opération sur le système.
    local model
    if ! model="$(read_configured_model)"; then
        log_error "Installation IA interrompue : modèle configuré invalide."
        return 1
    fi

    install_ollama_if_missing

    start_ollama_service

    ensure_model_available "$model"

    log_success "Moteur IA local installé et vérifié."
    log_warning "OPENCOACH_AI_ENABLED n'est pas modifié par l'installation du runtime."
    log_info "Le backend et les tâches planifiées OpenCoach restent indépendants d'Ollama."
}


if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
