# Slurm backend

This directory contains the active SSH-to-Slurm transport and three remote GPU workers. [`backend.py`](backend.py) creates a UUID request directory, writes `input.json` over SSH, submits the configured batch script, polls `squeue`/`sacct`, and reads `output.json`.

## Configuration

[`config.py`](config.py) loads the repository-root `.env` and uses:

- `SLURM_SSH_HOST` and `SLURM_PROXY_JUMP` for `ssh -J`.
- `SLURM_REMOTE_JOB_DIR` for per-request input/output directories.
- `SLURM_REMOTE_REPO_DIR` for code and virtual-environment paths on the worker.
- `SLURM_EMBEDDING_SCRIPT`, `SLURM_LLM_SCRIPT`, and `SLURM_GEMMA_SCRIPT` for batch script paths.
- `SLURM_POLL_INTERVAL`, `SLURM_ALLOCATION_TIMEOUT`, and `SLURM_COMPLETION_TIMEOUT` for job monitoring.

The selectable remote model identifiers are the literal allowlists in [`models.py`](models.py).

## Workers

- [`run_embedding.sbatch`](run_embedding.sbatch) activates `embedding/venv-embedding` and runs [`offline_embedding.py`](offline_embedding.py).
- [`run_llm.sbatch`](run_llm.sbatch) activates `vllm/venv-vllm` and runs [`offline_llm.py`](offline_llm.py).
- [`run_gemma.sbatch`](run_gemma.sbatch) activates `vllm/venv-vllm` and runs [`offline_gemma.py`](offline_gemma.py) with the adapter in `backend/assets/models/Gemma-3-12B-finetuned/`.

Embedding and AI-insight callers provide an Aquifer fallback in `backend/app/services/`. Gemma does not have a fallback. The Gemma worker loads one model and performs two generations: a GPA followed by diagnostic comments.

Remote request cleanup is implemented in `_cleanup()` but its call is currently disabled, so request directories remain under `SLURM_REMOTE_JOB_DIR`.
