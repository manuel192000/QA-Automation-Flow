#!/usr/bin/env bash
# Crea el repo en GitHub (tu cuenta) y hace el primer push desde esta carpeta.
# Requisito: haber ejecutado antes `gh auth login --web --git-protocol https`
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

GH="${GH:-/opt/homebrew/bin/gh}"
if ! command -v gh >/dev/null 2>&1 && [[ -x "$GH" ]]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi

REPO_NAME="${1:-qa-automation-flow}"
VISIBILITY="${VISIBILITY:-public}" # public | private (por defecto: público)

if ! gh auth status >/dev/null 2>&1; then
  echo "No hay sesión en GitHub. En la Terminal de Cursor ejecutá:"
  echo ""
  echo "  gh auth login --web --git-protocol https"
  echo ""
  echo "Seguí el navegador hasta que diga que estás logueado. Luego volvé a correr:"
  echo "  ./scripts/push-to-github.sh [nombre-del-repo-opcional]"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "El remote 'origin' ya existe. Haciendo push..."
  git push -u origin main
  echo "Listo."
  exit 0
fi

if [[ "$VISIBILITY" == "private" ]]; then
  gh repo create "$REPO_NAME" --private --source=. --remote=origin --push
else
  gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
fi

echo ""
echo "Repo creado y código subido. Revisá en GitHub el repo: $REPO_NAME"
