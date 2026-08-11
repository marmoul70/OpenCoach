#!/usr/bin/env bash

# OpenCoach - Logging library
#
# Provides standardized terminal logging functions.
#
# Usage:
#   source "path/to/log.sh"
#
# Available functions:
#   log_info
#   log_success
#   log_warning
#   log_error

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=colors.sh
source "$SCRIPT_DIR/colors.sh"

log_info() {
    printf '%b[INFO]%b %s\n' \
        "$OC_COLOR_BLUE" \
        "$OC_COLOR_RESET" \
        "$1"
}

log_success() {
    printf '%b[ OK ]%b %s\n' \
        "$OC_COLOR_GREEN" \
        "$OC_COLOR_RESET" \
        "$1"
}

log_warning() {
    printf '%b[WARN]%b %s\n' \
        "$OC_COLOR_YELLOW" \
        "$OC_COLOR_RESET" \
        "$1"
}

log_error() {
    printf '%b[FAIL]%b %s\n' \
        "$OC_COLOR_RED" \
        "$OC_COLOR_RESET" \
        "$1" >&2
}