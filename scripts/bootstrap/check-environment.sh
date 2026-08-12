#!/usr/bin/env bash

# OpenCoach - Environment check
#
# Verifies that the current system provides the basic
# environment required by OpenCoach.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/lib/log.sh
source "$PROJECT_ROOT/scripts/lib/log.sh"

# shellcheck source=scripts/lib/system.sh
source "$PROJECT_ROOT/scripts/lib/system.sh"

# shellcheck source=scripts/lib/dependencies.sh
source "$PROJECT_ROOT/scripts/lib/dependencies.sh"

# shellcheck source=scripts/lib/package-manager.sh
source "$PROJECT_ROOT/scripts/lib/package-manager.sh"

# shellcheck source=scripts/lib/packages.sh
source "$PROJECT_ROOT/scripts/lib/packages.sh"

# shellcheck source=scripts/lib/exit-codes.sh
source "$PROJECT_ROOT/scripts/lib/exit-codes.sh"

require_install_privileges() {
    if (( INSTALL_REQUESTED == 0 )); then
        return "$OPENCOACH_EXIT_SUCCESS"
    fi

    if (( EUID == 0 )); then
        return "$OPENCOACH_EXIT_SUCCESS"
    fi

    log_error "Le mode --install nécessite les privilèges administrateur."
    log_error "Relancez le script avec sudo :"
    if (( DEV_REQUESTED == 1 )); then
        log_error "sudo $0 --install --dev"
    else
        log_error "sudo $0 --install"
    fi

    return "$OPENCOACH_EXIT_PERMISSION_DENIED"
}

verify_required_commands() {
    local missing_commands=0

    for command_name in "${OPENCOACH_REQUIRED_COMMANDS[@]}"; do
        if require_command "$command_name"; then
            log_success "$command_name disponible"
        else
            log_error "$command_name est introuvable"
            ((missing_commands += 1))
        fi
    done

    if (( missing_commands > 0 )); then
        log_error "$missing_commands commande(s) requise(s) indisponible(s)"
        return "$OPENCOACH_EXIT_MISSING_DEPENDENCY"
    fi

    return "$OPENCOACH_EXIT_SUCCESS"
}

validate_environment() {
    local debian_version

    log_info "Validation globale de l'environnement"

    if ! is_debian; then
        log_error "Le système n'est pas Debian"
        return "$OPENCOACH_EXIT_GENERAL_ERROR"
    fi

    log_success "Debian détecté"

    debian_version="$(get_debian_version)"

    if [[ "$debian_version" != "13" ]]; then
        log_error "Debian 13 est requis (version détectée : $debian_version)"
        return "$OPENCOACH_EXIT_GENERAL_ERROR"
    fi

    log_success "Debian $debian_version détecté"

    if ! apt_is_usable; then
        log_error "APT n'est pas opérationnel"
        return "$OPENCOACH_EXIT_SYSTEM_ERROR"
    fi

    log_success "APT est opérationnel"

    if ! verify_required_commands; then
        return "$OPENCOACH_EXIT_MISSING_DEPENDENCY"
    fi

    log_success "Environnement de base valide"

    return "$OPENCOACH_EXIT_SUCCESS"
}

verify_required_packages() {
    local missing_packages=()

    while IFS= read -r package_name; do
        [[ -n "$package_name" ]] || continue
        missing_packages+=("$package_name")
    done < <(get_required_installations "${OPENCOACH_REQUIRED_PACKAGES[@]}")

    if (( ${#missing_packages[@]} == 0 )); then
        log_success "Tous les paquets OpenCoach sont installés"
        return "$OPENCOACH_EXIT_SUCCESS"
    fi

    log_warning "Paquets OpenCoach manquants : ${#missing_packages[@]}"

    for package_name in "${missing_packages[@]}"; do
        log_warning "  - $package_name"
    done

    return "$OPENCOACH_EXIT_MISSING_DEPENDENCY"
}

verify_available_packages() {
    local unavailable_packages=0

    for package_name in "${OPENCOACH_REQUIRED_PACKAGES[@]}"; do
        if package_is_available "$package_name"; then
            log_success "Paquet $package_name disponible dans APT"
        else
            log_error "Paquet $package_name indisponible dans APT"
            ((unavailable_packages += 1))
        fi
    done

    if (( unavailable_packages > 0 )); then
        log_error "$unavailable_packages paquet(s) requis indisponible(s) dans APT"
        return "$OPENCOACH_EXIT_MISSING_DEPENDENCY"
    fi

    return "$OPENCOACH_EXIT_SUCCESS"
}

get_installable_packages_for_environment() {
    local package_name

    for package_name in "${OPENCOACH_REQUIRED_PACKAGES[@]}"; do
        if ! is_package_installed "$package_name" &&
           package_is_available "$package_name"; then
            printf '%s\n' "$package_name"
        fi
    done

    if (( DEV_REQUESTED == 1 )); then
        for package_name in "${OPENCOACH_DEV_PACKAGES[@]}"; do
            if ! is_package_installed "$package_name" &&
               package_is_available "$package_name"; then
                printf '%s\n' "$package_name"
            fi
        done
    fi
}

INSTALL_REQUESTED=0
DEV_REQUESTED=0

while (( $# > 0 )); do
    case "$1" in
        "")
            ;;

        "--help"|"-h")
            printf '%s\n' "OpenCoach - Vérification de l'environnement"
            printf '\n'
            printf '%s\n' "Utilisation :"
            printf '  %s\n' "$0"
            printf '  %s --install\n' "$0"
            printf '  %s --install --dev\n' "$0"
            printf '  %s --help\n' "$0"
            printf '\n'
            printf '%s\n' "Options :"
            printf '  --install    Installe les dépendances manquantes.'
            printf '\n'
            printf '  --dev        Ajoute les outils de développement.'
            printf '\n'
            printf '  --help       Affiche cette aide.'
            printf '\n'
            exit "$OPENCOACH_EXIT_SUCCESS"
            ;;

        "--install")
            INSTALL_REQUESTED=1
            ;;

        "--dev")
            DEV_REQUESTED=1
            ;;

        *)
            printf 'Argument inconnu : %s\n' "$1" >&2
            printf 'Utilisation : %s [--install [--dev]|--help]\n' "$0" >&2
            exit "$OPENCOACH_EXIT_INVALID_ARGUMENT"
            ;;
    esac

    shift
done

if (( DEV_REQUESTED == 1 && INSTALL_REQUESTED == 0 )); then
    printf '%s\n' "Le mode --dev nécessite --install." >&2
    printf 'Utilisation : %s --install --dev\n' "$0" >&2
    exit "$OPENCOACH_EXIT_INVALID_ARGUMENT"
fi

if require_install_privileges; then
    :
else
    privilege_status=$?
    exit "$privilege_status"
fi

log_info "Vérification de l'environnement OpenCoach"

if validate_environment; then
    log_success "Validation globale de l'environnement réussie"
else
    validation_status=$?
    log_error "La validation globale de l'environnement a échoué."
    exit "$validation_status"
fi

printf '\n'
log_info "Vérification des paquets OpenCoach"

if ! verify_available_packages; then
    log_error "La vérification de disponibilité des paquets a échoué."
    exit "$OPENCOACH_EXIT_MISSING_DEPENDENCY"
fi

log_success "Tous les paquets requis sont disponibles dans APT"

if verify_required_packages; then
    log_success "Validation des paquets OpenCoach réussie"
else
    package_validation_status=$?

    if (( package_validation_status == OPENCOACH_EXIT_MISSING_DEPENDENCY )); then
        log_info "Des paquets requis sont absents et peuvent éventuellement être installés."
    else
        log_error "La validation des paquets OpenCoach a échoué."
        exit "$package_validation_status"
    fi
fi

installable_packages=()

while IFS= read -r package_name; do
    [[ -n "$package_name" ]] || continue
    installable_packages+=("$package_name")
done < <(get_installable_packages_for_environment)

if (( ${#installable_packages[@]} == 0 )); then
    log_success "Aucun paquet supplémentaire disponible pour installation"
else
    log_info "Paquets pouvant être installés : ${#installable_packages[@]}"

    for package_name in "${installable_packages[@]}"; do
        log_info "  - $package_name"
    done
fi

if (( INSTALL_REQUESTED == 0 )); then
    if (( ${#installable_packages[@]} > 0 )); then
        log_info "Des paquets peuvent être installés."
        log_info "Relancer avec --install pour effectuer l'installation."
    fi
else
    log_info "Mode installation activé."

    if (( ${#installable_packages[@]} > 0 )); then
        log_info "Installation des paquets manquants..."

        if (( DEV_REQUESTED == 1 )); then
            packages_to_install+=("${OPENCOACH_DEV_PACKAGES[@]}")
        fi

        if ! install_required_packages "${packages_to_install[@]}"; then
            log_error "L'installation des dépendances a échoué."
            exit "$OPENCOACH_EXIT_SYSTEM_ERROR"
        fi

        if ! verify_packages_installed "${packages_to_install[@]}"; then
            log_error "Vérification des dépendances échouée après installation."
            exit "$OPENCOACH_EXIT_MISSING_DEPENDENCY"
        fi

        if ! verify_packages_installed "${OPENCOACH_REQUIRED_PACKAGES[@]}"; then
            log_error "Vérification des dépendances échouée après installation."
            exit "$OPENCOACH_EXIT_MISSING_DEPENDENCY"
        fi

        log_success "Installation des dépendances terminée et vérifiée."
    else
        log_success "Aucune installation nécessaire."
    fi
fi

printf '\n'
log_info "Validation finale de l'environnement"

if ! verify_required_commands; then
    log_error "La validation finale de l'environnement a échoué."
    exit "$OPENCOACH_EXIT_MISSING_DEPENDENCY"
fi

log_success "Validation finale de l'environnement réussie"

exit "$OPENCOACH_EXIT_SUCCESS"
