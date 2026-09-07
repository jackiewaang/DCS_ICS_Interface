# DCS ICS Interface

DCS ICS Interface is a developer-facing React and FastAPI application for analysing REF impact case studies. It extracts editable sections from uploaded PDFs, runs AttentionMIL inference, generates AI insights, offers a separate fine-tuned Gemma assessment, and exports results as PDFs.

## Architecture

```text
Browser
  |
  v
React frontend served by Apache on Wagtail
  |
  | /api via ProxyPass + ProxyPassReverse
  v
FastAPI backend on Wagtail
  |-- SQLite: model configurations and submitted feedback
  |-- JSONL logs: user inference inputs and outputs
  |-- in-memory job store: active and recently completed API jobs
  |
  |-- primary --> Slurm GPU jobs on kudu
  |                |-- sentence embeddings
  |                |-- AI insights
  |                `-- fine-tuned Gemma assessment
  |
  `-- fallback --> Aquifer GPU services
                   |-- Qwen3-Embedding-4B
                   `-- Qwen3-4B-Instruct
```

Apache serves the compiled frontend and routes `/api` to FastAPI using `ProxyPass` and `ProxyPassReverse`. The deployment-specific routing is in `apache/conf/httpd.conf` on Wagtail; that file is not part of this repository.

Slurm is the primary execution environment because it provides access to higher-capacity GPUs. If Slurm embedding or AI-insight generation fails, the backend falls back to the Aquifer services. Aquifer has less GPU memory, so its fallback services use the Qwen3 4B embedding and instruction models configured in [`.env.example`](.env.example). Gemma uses its own Slurm-only pipeline and has no Aquifer fallback.

## Repository structure

- [`frontend/`](frontend/README.md) — React interface, temporary session history, result views, and PDF exports.
- [`backend/`](backend/README.md) — FastAPI API, AttentionMIL pipeline, persistence, and inference-service coordination.
- [`backend/slurmBackend/`](backend/slurmBackend/README.md) — SSH/Slurm transport and remote embedding, AI-insight, and Gemma workers.
- [`embedding/`](embedding/) — Aquifer fallback embedding service.
- [`vllm/`](vllm/) — environment for Aquifer vLLM and the remote vLLM workers.
- [`scripts/`](scripts/README.md) — setup, startup, and feedback-export scripts.
- [`backend/assets/models/`](backend/assets/models/) — AttentionMIL model packages and the fine-tuned Gemma adapter.

## Requirements

- Python 3.11 is the stable project version and should be used for compatibility.
- Node.js and npm compatible with Vite 7.
- CUDA-capable environments on Aquifer and the Slurm workers.
- SSH access from Wagtail to the configured Slurm host and proxy jump.
- Access to the Hugging Face models configured in [`.env.example`](.env.example) and [`backend/slurmBackend/models.py`](backend/slurmBackend/models.py).

The backend uses both installed English spaCy pipelines for different work:

- `en_core_web_sm` performs sentence segmentation, sentiment input preparation, and aggregate counts for organisations, people, locations, and money mentions.
- `en_core_web_trf` performs the detailed named-entity extraction used in the AttentionMIL feature vector and entity display.

The project uses three separate virtual environments:

- `backend/venv-backend` for FastAPI, feature extraction, SQLite, and CPU AttentionMIL inference.
- `embedding/venv-embedding` for the CUDA Sentence Transformers embedding service.
- `vllm/venv-vllm` for the CUDA vLLM service and remote LLM/Gemma workers.

## Clone and configure

```bash
git clone git@github.com:jackiewaang/DCS_ICS_Interface.git
cd DCS_ICS_Interface
cp .env.example .env
```

Update `.env` with the Wagtail, Aquifer, SSH, Slurm, remote repository, model, and timeout values for the deployment.

## Setup

Run the setup scripts from the repository root in the environments where each service will execute:

```bash
./scripts/backend/setup_backend.sh
./scripts/embedding/setup_embedding.sh
./scripts/vllm/setup_llm.sh
```

Backend setup installs both spaCy models and the NLTK VADER lexicon. Frontend packages are installed by `start_backend.sh` before it builds the production bundle.

## Run

On Aquifer, start the local fallback services:

```bash
./scripts/embedding/start_embedding.sh
./scripts/vllm/start_llm.sh
```

On Wagtail, start the backend and build/deploy the frontend:

```bash
./scripts/backend/start_backend.sh
```

The backend startup installs frontend packages, builds `frontend/dist/`, copies the result into `$HOME/apache/htdocs/`, loads `.env`, and starts FastAPI with Uvicorn. Apache is managed separately.

## AttentionMIL pipeline

The PDF upload endpoint uses the numbered REF headings to delimit the document and returns sections 1 (summary), 2 (underpinning research), and 4 (details of impact) for review. During inference, the backend:

1. combines the edited sections and calculates readability, sentiment, structural, monetary, and named-entity features;
2. segments the narrative into sentences and requests Qwen3 sentence embeddings;
3. passes the sentence embeddings and ordered case features to the selected AttentionMIL checkpoint;
4. returns the classification score, attention weights, feature gates, contribution values, and model metadata;
5. makes the completed MIL output available before AI-insight generation begins as a separate job.

Two AttentionMIL configurations are currently discovered from [`backend/assets/models/`](backend/assets/models/) and seeded into SQLite:

- **Quantile** — [`Qwen3-Embedding-4B-quantile/model_config.json`](backend/assets/models/Qwen3-Embedding-4B-quantile/model_config.json) was configured using the top and bottom 20% of GPA labels and distinguishes 4-star/high-impact cases from 1–2-star/low-impact cases.
- **Threshold** — [`Qwen3-Embedding-4B-threshold/model_config.json`](backend/assets/models/Qwen3-Embedding-4B-threshold/model_config.json) focuses on the boundary between 4-star and 3-star impact, using the configured 3.5 GPA threshold.

Both configurations use sentence-level Qwen3-Embedding-4B inputs, normalised case features, and gated feature fusion. The selected configuration controls the checkpoint, scaler, feature order, and classification interpretation.

## Job handling

MIL, AI-insight, and Gemma requests use asynchronous job endpoints. FastAPI creates a user-owned record in [`backend/app/services/job_store.py`](backend/app/services/job_store.py), returns a job ID immediately, and executes the blocking pipeline outside the event loop. The React client polls the matching status endpoint every 10 seconds until the job completes or fails.

Job records are held only in backend memory. Access is scoped by the browser-generated `X-User-ID`, completed records expire after one hour, and all records disappear when the backend restarts. AI insights are a separate job started after MIL completes; their polling continues while the user navigates within the application. Gemma is also a separate job and does not trigger MIL or AI-insight execution.

## Persistence and exports

The persistence layers have deliberately different roles:

- `backend/database.db` stores only seeded model configurations and submitted feedback.
- `logs-users/<user-id>/inferences.jsonl` and `gemma_inferences.jsonl` record user inputs and the corresponding logged outputs. They are operational/research logs, not the source for frontend history.
- The frontend holds MIL results, AI insights, and Gemma results temporarily in React state for the current browser session. Refreshing the page clears that history.

Users should export important MIL or Gemma results as PDFs before refreshing or closing the application.
