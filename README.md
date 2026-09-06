# DCS ICS Interface

React/Vite frontend and FastAPI backend for uploading REF impact case studies, running the trained AttentionMIL inference pipeline, browsing previous cases, and generating LLM review feedback.

## Project Structure

- `backend/` - FastAPI API server, SQLite database, model assets, inference pipeline, Slurm client/workers, and Python dependencies.
- `frontend/` - React development frontend built with Vite.
- `vllm/` - helper script for starting the local OpenAI-compatible vLLM server used by the LLM review feature.

## Requirements

- Python 3.11. The current backend script loads `Python/3.11.5-GCCcore-13.2.0` on the target cluster.
- Node.js 20.19+ or 22.12+. The frontend uses Vite 7, which requires a recent Node runtime.
- A CUDA-capable environment for vLLM if LLM review generation is required.
- The required embedding/model assets under `backend/assets/models/`.
- For vLLM review generation, the chat model must already be available through Hugging Face cache or equivalent local model access. Some models may require Hugging Face authentication before they can be downloaded or loaded.

Key pinned backend packages include FastAPI `0.135.1`, Uvicorn `0.41.0`, Sentence Transformers `5.3.0`, PyTorch `2.11.0`, and vLLM `0.25.1`.

## Backend Setup

Create the virtual environment inside the `backend/` directory. The existing scripts expect the environment to be named `venv311`.

```bash
cd backend
python3.11 -m venv venv311
source venv311/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you are running on the cluster environment used by this project, load Python first:

```bash
module load Python/3.11.5-GCCcore-13.2.0
```

## Run The Backend

Run the backend from inside the `backend/` directory:

```bash
cd backend
./app/start.sh
```

The script starts FastAPI with Uvicorn:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 11005
```

On first startup, the FastAPI lifespan hook calls `init_db()`. If the SQLite database does not already exist, this creates the database tables and seeds model configuration rows from `backend/assets/models/**/model_config.json`.

Backend URLs:

- Health check: `http://localhost:11005/`
- API docs: `http://localhost:11005/docs`
- API base: `http://localhost:11005/api`

The current startup script is working-directory sensitive because it activates `venv311/bin/activate` with a relative path. Run it from `backend/`.

## Frontend Setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite will print the development URL, usually `http://localhost:5173`.

The frontend currently uses:

```js
const API_BASE = "/api";
```

For local development, make sure requests to `/api` reach the FastAPI backend.

The frontend also supports sample-data mode:

```bash
VITE_USE_SAMPLE_DATA=true npm run dev
```

## vLLM Setup

The LLM review feature expects an OpenAI-compatible vLLM server on port `8000`.

Run the script from inside the `vllm/` directory:

```bash
cd vllm
./start_llm.sh
```

The model must already be available to the environment, for example through the Hugging Face cache. If the model is gated or private, make sure Hugging Face authentication is configured before starting vLLM.

The backend LLM client calls:

```text
http://localhost:8000/v1
```

## Typical Development Workflow

Use three terminals when running the complete development stack:

```bash
# Terminal 1
cd backend
./app/start.sh
```

```bash
# Terminal 2
cd frontend
npm run dev
```

```bash
# Terminal 3, optional for LLM review generation
cd vllm
./start_llm.sh
```

The core upload and model inference flow can run without vLLM, but LLM review generation requires the vLLM server.

## Slurm-first inference with Aquifer fallback

Embedding generation and LLM feedback now submit GPU jobs through
`backend/slurmBackend` first. If submission, allocation, execution, result parsing,
or either configured Slurm timeout fails, the backend logs the failure and retries
the same operation through the existing local services (Aquifer):

- Embeddings: `http://localhost:8001/embed`
- LLM feedback: the OpenAI-compatible endpoint configured by `VLLM_BASE_URL`

Copy `.env.example` to `.env` in the repository root and configure the Slurm
connection there. The remote repository must use
the same layout, including these relocated script paths:

```text
DCS_ICS_Interface/backend/slurmBackend/run_embedding.sbatch
DCS_ICS_Interface/backend/slurmBackend/run_llm.sbatch
DCS_ICS_Interface/backend/slurmBackend/run_gemma.sbatch
```

Set `SLURM_GEMMA_SCRIPT` to the remote path of `run_gemma.sbatch`. The Gemma
assessment endpoint loads the fine-tuned adapter from
`backend/assets/models/Gemma-3-12B-finetuned/` in the remote repository and
writes its request log to `logs-users/<user-id>/gemma_inferences.jsonl`; it does
not save Gemma inferences to the application database.

The user-selectable remote model allowlists are defined in
`backend/slurmBackend/models.py`. Aquifer fallback keeps its existing fixed
embedding and LLM models.

## Database Initialisation

The backend uses a local SQLite database. On first backend startup, `app.database.init_db.init_db()` checks whether the DB file exists. If it does not exist, it creates tables through SQLAlchemy metadata and seeds model configurations from the model asset folders.

## Inference Pipeline Overview

The main inference path is handled by `backend/app/pipeline/manager.py`.

At a high level:

1. The frontend uploads a PDF to `/api/cases/upload`.
2. The backend extracts text from the PDF and splits it into REF sections.
3. The frontend sends edited sections to `/api/analysis/inference` with a selected `config_id`.
4. The backend loads the selected model configuration from the database.
5. `feature_extractor` computes GTF-style textual features, readability metrics, sentiment statistics, money values, word/paragraph counts, and spaCy named entities.
6. Entity counts are added into the feature set in the order expected by the selected model config.
7. `embedder` builds sentence-level or full-document inputs and generates embeddings using the configured embedding model.
8. The pipeline saves the generated embeddings under `backend/embeddings/`.
9. `ModelRunner` loads the trained AttentionMIL checkpoint and optional scaler, runs prediction, and returns score, label, attention weights, feature gates, and contribution estimates.
10. The API saves the document, feature payload, inference output, and attention rows to the database.
11. A background LLM review task is scheduled. If vLLM is running, it generates structured review feedback and stores it with the inference.

The model configuration is important: embedding model, input granularity, feature order, scaler, and checkpoint must match how the model was trained.

## Future Static Frontend Deployment

The current setup uses Vite in development mode. Later, the frontend can be built with:

```bash
cd frontend
npm run build
```

The generated `frontend/dist/` files can then be served by FastAPI or by a production web server. In that deployment shape, users should only need to start the FastAPI backend, which will serve both API routes and the built frontend assets.
