#!/usr/bin/env bash

# OpenCoach - Bash color definitions
#
# This file contains ANSI escape sequences used by OpenCoach
# command-line scripts.

if [[ -z "${OPENCOACH_COLORS_LOADED:-}" ]]; then
    readonly OPENCOACH_COLORS_LOADED=1

    readonly OC_COLOR_RESET=$'\033[0m'

    readonly OC_COLOR_RED=$'\033[31m'
    readonly OC_COLOR_GREEN=$'\033[32m'
    readonly OC_COLOR_YELLOW=$'\033[33m'
    readonly OC_COLOR_BLUE=$'\033[34m'
    readonly OC_COLOR_MAGENTA=$'\033[35m'
    readonly OC_COLOR_CYAN=$'\033[36m'
    readonly OC_COLOR_WHITE=$'\033[37m'
fi