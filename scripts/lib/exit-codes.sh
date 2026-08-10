#!/usr/bin/env bash

# OpenCoach - Exit codes
#
# Centralized exit codes used by OpenCoach scripts.

if ! declare -p OPENCOACH_EXIT_SUCCESS >/dev/null 2>&1; then
    readonly OPENCOACH_EXIT_SUCCESS=0
fi

if ! declare -p OPENCOACH_EXIT_GENERAL_ERROR >/dev/null 2>&1; then
    readonly OPENCOACH_EXIT_GENERAL_ERROR=1
fi

if ! declare -p OPENCOACH_EXIT_INVALID_ARGUMENT >/dev/null 2>&1; then
    readonly OPENCOACH_EXIT_INVALID_ARGUMENT=2
fi

if ! declare -p OPENCOACH_EXIT_MISSING_DEPENDENCY >/dev/null 2>&1; then
    readonly OPENCOACH_EXIT_MISSING_DEPENDENCY=3
fi

if ! declare -p OPENCOACH_EXIT_PERMISSION_DENIED >/dev/null 2>&1; then
    readonly OPENCOACH_EXIT_PERMISSION_DENIED=4
fi

if ! declare -p OPENCOACH_EXIT_SYSTEM_ERROR >/dev/null 2>&1; then
    readonly OPENCOACH_EXIT_SYSTEM_ERROR=5
fi
