#!/bin/bash
module load Python/3.11.5-GCCcore-13.2.0
module load CUDA/12.8.0

source ../backend/venv311/bin/activate

MODEL="Qwen/Qwen3-4B-Instruct-2507"

exec vllm serve "$MODEL" \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.6 \
    --port 8000 \
    --host 0.0.0.0
