#!/bin/bash
#
#SBATCH --job-name=ref-llm
#SBATCH --partition=gecko
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --time=00:10:00
#
#SBATCH --output=joboutput_%j.out
#SBATCH --error=joboutput_%j.err

set -euo pipefail

REMOTE_DIR="$1"
REMOTE_REPO_DIR="$2"

source /etc/profile.d/modules.sh
module load CUDA

source "$REMOTE_REPO_DIR/vllm/venv-vllm/bin/activate"

set -a
source "$REMOTE_REPO_DIR/.env"
set +a

export PYTHONPATH="$REMOTE_REPO_DIR/backend${PYTHONPATH:+:$PYTHONPATH}"
python "$REMOTE_REPO_DIR/backend/slurmBackend/offline_llm.py" "$REMOTE_DIR"
