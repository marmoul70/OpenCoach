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

shellcheck -x -P scripts/bootstrap scripts/bootstrap/install.sh scripts/bootstrap/install-ai.sh scripts/bootstrap/check-environment.sh scripts/bootstrap/install-application.sh scripts/bootstrap/install-services.sh scripts/bootstrap/upgrade.sh scripts/deploy-frontend.sh scripts/deploy_frontend.sh scripts/maintenance/check-version-consistency.sh scripts/maintenance/check-ai-model-config.sh tests/test-deploy-frontend.sh tests/test-nginx-bootstrap.sh tests/test-install-ai.sh tests/test-install-ai-runtime.sh tests/test-install-ai-flow.sh

echo
echo "[ OK ] ShellCheck terminé sans erreur."