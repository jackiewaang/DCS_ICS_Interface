#!/bin/bash
set -e

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/backend"
VENV="$APP_DIR/venv-backend"

#module load Python/3.11.5-GCCcore-13.2.0

if [[ ! -d "$VENV" ]]; then
    python3.11 -m venv "$VENV"
    "$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"
fi
