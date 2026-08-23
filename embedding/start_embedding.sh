#!/bin/bash
# Loads the HPC runtime and starts the standalone embedding API.

module load Python/3.11.5-GCCcore-13.2.0
module load CUDA/12.8.0

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$REPO_ROOT/backend/venv311/bin/activate"
cd "$REPO_ROOT" || exit 1

exec uvicorn embedding.server:app --host 0.0.0.0 --port 8001
