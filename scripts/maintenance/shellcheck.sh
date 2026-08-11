#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "========================================"
echo " OpenCoach - ShellCheck"
echo "========================================"
echo

if ! command -v shellcheck >/dev/null 2>&1; then
    echo "[FAIL] ShellCheck n'est pas installé."
    echo "       Installez-le avec : sudo apt install shellcheck"
    exit 3
fi

echo "[INFO] Analyse des scripts OpenCoach..."

shellcheck -x scripts/bootstrap/check-environment.sh

echo
echo "[ OK ] ShellCheck terminé sans erreur."