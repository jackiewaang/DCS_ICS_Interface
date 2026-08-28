#!/bin/bash
set -u

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
SERVER_PIDS=()

cleanup() {
    if ((${#SERVER_PIDS[@]})); then
        kill "${SERVER_PIDS[@]}" 2>/dev/null || true
        wait "${SERVER_PIDS[@]}" 2>/dev/null || true
    fi
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

(
    cd "$SCRIPT_DIR/embedding" || exit 1
    exec ./start_embedding.sh
) &
SERVER_PIDS+=("$!")

(
    cd "$SCRIPT_DIR/vllm" || exit 1
    exec ./start_llm.sh
) &
SERVER_PIDS+=("$!")

echo "Embedding server started on port 8001 (PID ${SERVER_PIDS[0]})"
echo "vLLM server started on port 8000 (PID ${SERVER_PIDS[1]})"
echo "Press Ctrl+C to stop both servers."

wait -n "${SERVER_PIDS[@]}"
