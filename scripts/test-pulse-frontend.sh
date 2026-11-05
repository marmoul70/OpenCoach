#!/usr/bin/env bash
set -Eeuo pipefail

BRANCH="feature/opencoach-pulse-design-system"
TARGET_DIR="${1:-$HOME/opencoach-pulse-test}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Erreur : lance ce script depuis un clone Git du dépôt OpenCoach."
  exit 1
}

command -v git >/dev/null || { echo "git est requis."; exit 1; }
command -v node >/dev/null || { echo "Node.js est requis."; exit 1; }
command -v npm >/dev/null || { echo "npm est requis."; exit 1; }

if [[ -e "$TARGET_DIR" ]]; then
  echo "Arrêt : le dossier cible existe déjà : $TARGET_DIR"
  echo "Choisis un autre chemin en premier argument. Aucun fichier existant n'a été touché."
  exit 1
fi

REMOTE_URL="$(git -C "$REPO_ROOT" remote get-url origin)"
echo "Dépôt : $REMOTE_URL"
echo "Branche isolée : $BRANCH"
echo "Dossier de test : $TARGET_DIR"
echo
echo "Récupération de la branche distante..."
git -C "$REPO_ROOT" fetch --no-tags origin "$BRANCH"
PULSE_COMMIT="$(git -C "$REPO_ROOT" rev-parse FETCH_HEAD)"

echo "Création d'un worktree indépendant sur $PULSE_COMMIT..."
git -C "$REPO_ROOT" worktree add --detach "$TARGET_DIR" "$PULSE_COMMIT"

cd "$TARGET_DIR/frontend"

echo
echo "Installation des dépendances verrouillées..."
npm ci

echo
echo "Compilation de production (TypeScript + Vite)..."
npm run build

echo
echo "Build terminé. Démarrage du frontend de test..."
echo "Backend API proxifié vers http://127.0.0.1:8000 (configuration Vite existante)."
echo "Pour tester depuis un autre appareil du réseau, ouvre :"
echo "  http://$(hostname -I 2>/dev/null | awk '{print $1}'):5173"
echo "Arrêt du serveur : Ctrl+C"
echo
npm run dev -- --host 0.0.0.0 --port 5173 --strictPort
