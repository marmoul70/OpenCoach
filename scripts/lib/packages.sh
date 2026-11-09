#!/usr/bin/env bash

# OpenCoach - Debian package definitions
#
# Centralized list of Debian packages required by OpenCoach.

readonly OPENCOACH_REQUIRED_PACKAGES=(
    bash
    git
    python3
    python3-venv
    python3-pip
    nodejs
    npm
    nginx
    curl
    ca-certificates
)

readonly OPENCOACH_DEV_PACKAGES=(
    shellcheck
)
