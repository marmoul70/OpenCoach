# OpenCoach — Package Manager

## Purpose

OpenCoach uses Debian's APT package manager for system-level
dependency management.

The package manager integration is located in:

Detection

The library provides:

has_apt — checks whether apt-get is available.
apt_is_usable — verifies that APT can be queried.

Both functions return standard Unix exit codes:

0 — success.
non-zero — failure.
Package definitions

Required Debian packages are centralized in:

scripts/lib/packages.sh

The current list is:

bash
git
Package availability

The bootstrap diagnostic uses:

apt-cache show <package>

to determine whether a package is known to the configured APT repositories.

This does not install or modify packages.

Installation

No package installation is performed by the current implementation.

Installation automation will be introduced in a later mission after
the detection and validation mechanisms have been established.

Architecture
check-environment.sh
        │
        ├── package-manager.sh
        │       ├── has_apt()
        │       └── apt_is_usable()
        │
        └── packages.sh
                └── OPENCOACH_REQUIRED_PACKAGES
scripts/lib/package-manager.sh