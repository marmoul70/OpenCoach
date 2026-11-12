#!/usr/bin/env bash

# Compatibilité avec l'ancien nom snake_case.
# Le déploiement est centralisé dans deploy-frontend.sh.

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/deploy-frontend.sh" "$@"
