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

# shellcheck source=../lib/dependencies.sh
source "$PROJECT_ROOT/scripts/lib/dependencies.sh"

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

available_dependencies=0
missing_dependencies=0

for command_name in "${OPENCOACH_REQUIRED_COMMANDS[@]}"; do
    if require_command "$command_name"; then
        log_success "$command_name disponible"
        ((available_dependencies += 1))
    else
        log_error "$command_name est introuvable"
        ((missing_dependencies += 1))
    fi
done

log_info "Résumé des dépendances"

if (( missing_dependencies > 0 )); then
    log_error "$missing_dependencies dépendance(s) manquante(s)"
    exit 1
fi

log_success "$available_dependencies dépendance(s) disponible(s)"
log_success "Environnement de base valide"

log_success "Environnement de base valide"