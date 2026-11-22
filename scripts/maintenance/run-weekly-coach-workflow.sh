#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

PYTHON_BIN="${OPENCOACH_PYTHON:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
    if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
        PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
    else
        PYTHON_BIN="python3"
    fi
fi

# Évite deux clôtures hebdomadaires concurrentes (cron + lancement manuel).
LOCK_FILE="${TMPDIR:-/tmp}/opencoach-weekly-coach-workflow.lock"
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    echo "[INFO] Un workflow hebdomadaire OpenCoach est déjà en cours."
    exit 0
fi

echo "[INFO] Démarrage du workflow hebdomadaire OpenCoach."
echo "[INFO] Racine : ${PROJECT_ROOT}"
echo "[INFO] Python : ${PYTHON_BIN}"

exec "${PYTHON_BIN}" -m opencoach.commands.run_weekly_debrief_workflow "$@"
