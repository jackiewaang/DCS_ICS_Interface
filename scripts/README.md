# Scripts

Run these scripts from the repository root.

## Setup

- [`backend/setup_backend.sh`](backend/setup_backend.sh) creates `backend/venv-backend`, installs `backend/requirements.txt`, and ensures both spaCy models and the NLTK VADER lexicon are installed.
- [`embedding/setup_embedding.sh`](embedding/setup_embedding.sh) creates `embedding/venv-embedding` and installs `embedding/requirements.txt`.
- [`vllm/setup_llm.sh`](vllm/setup_llm.sh) creates `vllm/venv-vllm` and installs `vllm/requirements.txt`.

Each setup script installs only when its target virtual-environment directory does not already exist.

## Startup

- [`embedding/start_embedding.sh`](embedding/start_embedding.sh) selects CUDA device 0, loads `.env`, and serves `embedding.server:app` at `HOST:AQUIFER_EMBEDDING_PORT`.
- [`vllm/start_llm.sh`](vllm/start_llm.sh) selects CUDA device 0, loads `.env`, and runs `vllm serve` using the configured Aquifer LLM variables.
- [`backend/start_backend.sh`](backend/start_backend.sh) installs frontend packages, builds the frontend, copies the build into `$HOME/apache/htdocs/`, loads `.env`, and runs Uvicorn at `HOST:BACKEND_SERVER_PORT`.

## Feedback export

[`export_feedback.py`](export_feedback.py) reads the `feedback` table from `backend/database.db` and writes `feedback.csv` by default. An output path may be supplied as its first argument:

```bash
backend/venv-backend/bin/python scripts/export_feedback.py exported-feedback.csv
```
