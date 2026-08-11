#!/usr/bin/env bash

# OpenCoach - System utilities
#
# Common functions used by OpenCoach installation and maintenance scripts.

require_command() {
    local command_name="$1"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "ERREUR : la commande '$command_name' n'est pas installée." >&2
        return 1
    fi
}

is_debian() {
    [[ -f /etc/os-release ]] || return 1

    # shellcheck disable=SC1091
    source /etc/os-release

    [[ "${ID:-}" == "debian" ]]
}

get_debian_version() {
    [[ -f /etc/os-release ]] || return 1

    # shellcheck disable=SC1091
    source /etc/os-release

    printf '%s\n' "${VERSION_ID:-unknown}"
}