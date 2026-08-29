#!/bin/bash
set -e

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"

cd "$FRONTEND_DIR"
npm run build
mkdir -p "$HOME/apache/htdocs"
cp -rf dist/* "$HOME/apache/htdocs/"

# module load Python/3.11.5-GCCcore-13.2.0 - uncomment to load Python module if not loaded
source "$APP_DIR/venv-backend/bin/activate"

set -a
source "$APP_DIR/.env"
set +a

export PYTHONSAFEPATH=1
cd "$APP_DIR"
exec python3.11 -P -m uvicorn app.main:app --host "$HOST" --port "$BACKEND_SERVER_PORT"
