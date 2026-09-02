#!/bin/bash
set -e

export CUDA_VISIBLE_DEVICES=0

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/vllm"

source "$APP_DIR/venv-vllm/bin/activate"

set -a
source "$REPO_ROOT/.env"
set +a

exec vllm serve "$AQUIFER_LLM_MODEL" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
    --quantization "$QUANTIZATION" \
    --port "$AQUIFER_LLM_PORT" \
    --host "$HOST"
