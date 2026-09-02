#!/bin/bash
set -e

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"

# Build frontend and copy to htdocs
cd "$FRONTEND_DIR"
npm run build
mkdir -p "$HOME/apache/htdocs"
cp -rf dist/* "$HOME/apache/htdocs/"

source "$APP_DIR/venv-backend/bin/activate"

set -a
source "$REPO_ROOT/.env"
set +a

export PYTHONSAFEPATH=1
cd "$APP_DIR"
exec python3.11 -P -m uvicorn app.main:app --host "$HOST" --port "$BACKEND_SERVER_PORT"
