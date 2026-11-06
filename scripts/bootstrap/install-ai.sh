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

    python3 - "$ENV_FILE" "$DEFAULT_MODEL" <<'PYTHON'
import sys
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

lines = env_path.read_text(encoding="utf-8").splitlines()
updated = []
seen = set()
for line in lines:
    if "=" not in line or line.lstrip().startswith("#"):
        updated.append(line)
        continue

    key, current = line.split("=", 1)
    key = key.strip()
    if key not in defaults:
        updated.append(line)
        continue

    if key in seen:
        continue
    seen.add(key)

    if current.strip().strip("'").strip('"'):
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

if updated != lines:
    env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
PYTHON

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

    for attempt in {1..30}; do
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

    install_ollama_if_missing

    start_ollama_service

    local model
    model="$(read_configured_model)"

    ensure_model_available "$model"

    log_success "Moteur IA local installé et vérifié."
    log_warning "OPENCOACH_AI_ENABLED n'est pas modifié par l'installation du runtime."
    log_info "Le backend et les tâches planifiées OpenCoach restent indépendants d'Ollama."
}


main "$@"
