#!/bin/bash
set -e

export CUDA_VISIBLE_DEVICES=0

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/vllm"

#module load Python/3.11.5-GCCcore-13.2.0 - uncomment to load Python module if not loaded
#module load CUDA/12.8.0 - uncomment to load CUDA
source "$APP_DIR/venv-vllm/bin/activate"

set -a
source "$APP_DIR/.env"
set +a

exec vllm serve "$LLM_MODEL_NAME" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
    --quantization bitsandbytes \
    --port "$VLLM_SERVER_PORT" \
    --host "$HOST"
