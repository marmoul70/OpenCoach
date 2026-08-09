#!/usr/bin/env bash

# OpenCoach - Package manager utilities
#
# Provides helpers for detecting and interacting with
# the system package manager.

has_apt() {
    command -v apt-get >/dev/null 2>&1
}

apt_is_usable() {
    has_apt || return 1

    apt-get --version >/dev/null 2>&1 || return 1

    apt-get indextargets >/dev/null 2>&1
}

is_package_installed() {
    local package_name="$1"

    dpkg-query \
        --show \
        --showformat='${Status}\n' \
        "$package_name" 2>/dev/null |
        grep -q '^install ok installed$'
}

get_missing_packages() {
    local package_name

    for package_name in "$@"; do
        if ! is_package_installed "$package_name"; then
            printf '%s\n' "$package_name"
        fi
    done
}

install_packages() {
    local dry_run=0

    if [[ "${1:-}" == "--dry-run" ]]; then
        dry_run=1
        shift
    fi

    if ! apt_is_usable; then
        return 1
    fi

    if (( $# == 0 )); then
        return 0
    fi

    if (( dry_run == 1 )); then
        printf '[DRY-RUN] Installation :'
        printf ' %s' "$@"
        printf '\n'
        return 0
    fi

    sudo apt-get install -y "$@"
}

package_is_available() {
    local package_name="${1:-}"

    [[ -n "$package_name" ]] || return 1

    apt-cache show "$package_name" >/dev/null 2>&1
}

get_unavailable_packages() {
    local package_name

    for package_name in "$@"; do
        if ! package_is_available "$package_name"; then
            printf '%s\n' "$package_name"
        fi
    done
}

validate_packages() {
    local package_name

    if ! apt_is_usable; then
        return 1
    fi

    for package_name in "$@"; do
        if [[ -z "$package_name" ]]; then
            return 1
        fi

        if ! package_is_available "$package_name"; then
            return 1
        fi
    done

    return 0
}

get_installable_packages() {
    local package_name

    for package_name in "$@"; do
        if ! is_package_installed "$package_name" &&
           package_is_available "$package_name"; then
            printf '%s\n' "$package_name"
        fi
    done
}

packages_installation_required() {
    local package_name

    for package_name in "$@"; do
        if ! is_package_installed "$package_name"; then
            return 0
        fi
    done

    return 1
}

get_required_installations() {
    local package_name

    for package_name in "$@"; do
        if ! is_package_installed "$package_name"; then
            printf '%s\n' "$package_name"
        fi
    done
}

validate_installation_list() {
    local package_name

    if ! apt_is_usable; then
        return 1
    fi

    for package_name in "$@"; do
        if [[ -z "$package_name" ]]; then
            return 1
        fi

        if is_package_installed "$package_name"; then
            continue
        fi

        if ! package_is_available "$package_name"; then
            printf 'Paquet indisponible : %s\n' "$package_name" >&2
            return 1
        fi
    done

    return 0
}

install_required_packages() {
    local package_name
    local -a packages_to_install=()

    if (( $# == 0 )); then
        return 0
    fi

    if ! validate_installation_list "$@"; then
        return 1
    fi

    while IFS= read -r package_name; do
        [[ -n "$package_name" ]] || continue
        packages_to_install+=("$package_name")
    done < <(get_required_installations "$@")

    if (( ${#packages_to_install[@]} == 0 )); then
        return 0
    fi

    install_packages "${packages_to_install[@]}"
}

verify_packages_installed() {
    local package_name

    for package_name in "$@"; do
        if ! is_package_installed "$package_name"; then
            printf 'Paquet non installé : %s\n' "$package_name" >&2
            return 1
        fi
    done

    return 0
}

install_required_packages() {
    local package_name
    local -a packages_to_install=()

    if (( $# == 0 )); then
        return 0
    fi

    if ! validate_installation_list "$@"; then
        printf 'Validation des paquets impossible.\n' >&2
        return 1
    fi

    while IFS= read -r package_name; do
        [[ -n "$package_name" ]] || continue
        packages_to_install+=("$package_name")
    done < <(get_required_installations "$@")

    if (( ${#packages_to_install[@]} == 0 )); then
        return 0
    fi

    if ! install_packages "${packages_to_install[@]}"; then
        printf 'Installation des paquets échouée.\n' >&2
        return 1
    fi

    return 0
}