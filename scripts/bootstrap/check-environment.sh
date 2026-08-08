#!/usr/bin/env bash

# OpenCoach - Environment check
#
# Verifies that the current system provides the basic
# environment required by OpenCoach.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=../lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

# shellcheck source=../lib/system.sh
source "$PROJECT_ROOT/scripts/lib/system.sh"

log_info "Vérification de l'environnement OpenCoach"

if is_debian; then
    log_success "Debian détecté"
else
    log_error "Le système n'est pas Debian"
    exit 1
fi

DEBIAN_VERSION="$(get_debian_version)"

if [[ "$DEBIAN_VERSION" == "13" ]]; then
    log_success "Debian $DEBIAN_VERSION détecté"
else
    log_error "Debian 13 est requis (version détectée : $DEBIAN_VERSION)"
    exit 1
fi

if require_command bash; then
    log_success "Bash disponible"
else
    log_error "Bash est introuvable"
    exit 1
fi

if require_command git; then
    log_success "Git disponible"
else
    log_error "Git est introuvable"
    exit 1
fi

log_success "Environnement de base valide"