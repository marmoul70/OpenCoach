#!/usr/bin/env bash

# OpenCoach - Debian package definitions
#
# Centralized list of Debian packages required by OpenCoach.

readonly OPENCOACH_REQUIRED_PACKAGES=(
    bash
    git
)

readonly OPENCOACH_DEV_PACKAGES=(
    shellcheck
)