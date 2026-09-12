# Slurm backend

This directory contains the active SSH-to-Slurm transport and three remote GPU workers. [`backend.py`](backend.py) creates a UUID request directory, writes `input.json` over SSH, submits the configured batch script, polls `squeue`/`sacct`, and reads `output.json`.

## Configuration

[`config.py`](config.py) loads the repository-root `.env` and uses:

- `SLURM_SSH_HOST` and `SLURM_PROXY_JUMP` for `ssh -J`.
- `SLURM_REMOTE_JOB_DIR` for per-request input/output directories.
- `SLURM_REMOTE_REPO_DIR` for code and virtual-environment paths on the worker.
- `SLURM_EMBEDDING_SCRIPT`, `SLURM_LLM_SCRIPT`, and `SLURM_GEMMA_SCRIPT` for batch script paths.
- `SLURM_POLL_INTERVAL`, `SLURM_ALLOCATION_TIMEOUT`, and `SLURM_COMPLETION_TIMEOUT` for job monitoring.

The selectable remote models are defined in [`models.py`](models.py). For LLMs,
add model IDs to `ada_models` (partition `wmlg-ada`), `gecko_models`, or both.
`SLURM_LLM_MODELS` is their deduplicated union. Models in both lists try
`wmlg-ada` first, then `gecko` only if allocation times out. Models in one list
only use that partition; unknown models are rejected before submission.

Each attempt gets the full `SLURM_ALLOCATION_TIMEOUT` and its own directory.
The timed-out job is cancelled before fallback; cancellation failures stop the
request. Submission errors, terminal job failures, and completion timeouts do
not trigger partition fallback. Exhausting eligible partitions raises
`SlurmAllocationTimeout`. Existing application-level fallbacks still apply.
Partition selection overrides the LLM script's default via `sbatch --partition`;
resources and environment remain the same. Embedding jobs continue using their
script defaults.

The separate fine-tuned Gemma pipeline uses `gemma_partitions` in `models.py`,
defaulting to `["wmlg-ada", "gecko"]`, with the same timeout and cancellation
rules. Remove `"gecko"` to make Gemma ada-only. It still uses `run_gemma.sbatch`
and its dedicated prompts and adapter; it is not added to `SLURM_LLM_MODELS`
or the MIL feedback pipeline.

## Workers

- [`run_embedding.sbatch`](run_embedding.sbatch) activates `embedding/venv-embedding` and runs [`offline_embedding.py`](offline_embedding.py).
- [`run_llm.sbatch`](run_llm.sbatch) activates `vllm/venv-vllm` and runs [`offline_llm.py`](offline_llm.py).
- [`run_gemma.sbatch`](run_gemma.sbatch) activates `vllm/venv-vllm` and runs [`offline_gemma.py`](offline_gemma.py) with the adapter in `backend/assets/models/Gemma-3-12B-finetuned/`.

Embedding and AI-insight callers provide an Aquifer fallback in `backend/app/services/`. Gemma does not have a fallback. The Gemma worker loads one model and performs two generations: a GPA followed by diagnostic comments.

Remote request directories are removed by `_cleanup()` after each attempt.

Run the mocked partition tests from the repository root:
`python -m unittest backend.slurmBackend.test_partition_routing`.
