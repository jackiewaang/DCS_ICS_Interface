#!/bin/bash
set -e

export CUDA_VISIBLE_DEVICES=0 # Use Titan RTX 24GB on Aquifer

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/embedding"

source "$APP_DIR/venv-embedding/bin/activate"

set -a
source "$REPO_ROOT/.env"
set +a

cd "$REPO_ROOT"
exec uvicorn embedding.server:app --host "$HOST" --port "$AQUIFER_EMBEDDING_PORT"
