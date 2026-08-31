#!/bin/bash
#
#SBATCH --job-name=ref-embedding
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

source "$REMOTE_REPO_DIR/embedding/venv-embedding/bin/activate"

# test_job.py must read "$REMOTE_DIR/input.json" and write
# "$REMOTE_DIR/output.json" before exiting successfully.
TEST_JOB_SCRIPT="${TEST_JOB_SCRIPT:-$REMOTE_REPO_DIR/slurmBackend/test_job.py}"
python "$TEST_JOB_SCRIPT" "$REMOTE_DIR" embedding
