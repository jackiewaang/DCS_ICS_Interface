#!/bin/bash
set -e

export CUDA_VISIBLE_DEVICES=0

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/embedding"

#module load Python/3.11.5-GCCcore-13.2.0
#module load CUDA/12.8.0
source "$APP_DIR/venv-embedding/bin/activate"

set -a
source "$APP_DIR/.env"
set +a

cd "$REPO_ROOT"
exec uvicorn embedding.server:app --host "$HOST" --port "$EMBEDDING_SERVER_PORT"
