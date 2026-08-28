#!/bin/bash
set -e

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/backend"

module load Python/3.11.5-GCCcore-13.2.0
source "$APP_DIR/venv-backend/bin/activate"

set -a
source "$APP_DIR/.env"
set +a

export PYTHONSAFEPATH=1
cd "$APP_DIR"
exec python -P -m uvicorn app.main:app --host "$HOST" --port "$BACKEND_SERVER_PORT"
