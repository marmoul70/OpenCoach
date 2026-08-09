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