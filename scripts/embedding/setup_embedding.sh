#!/bin/bash
set -e

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/embedding"
VENV="$APP_DIR/venv-embedding"

# Install Embedding dependencies
if [[ ! -d "$VENV" ]]; then
    python3.11 -m venv "$VENV"
    "$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"
fi
