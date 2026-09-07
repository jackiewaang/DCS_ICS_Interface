# Backend

The backend is a FastAPI application rooted at [`app/main.py`](app/main.py). Its lifespan initialises the SQLite database, and it registers the cases, analysis, Gemma, and feedback routers under `/api`.

## Layout

- [`app/api/endpoints/`](app/api/endpoints/) defines PDF upload, model/runtime metadata, asynchronous MIL and AI-insight jobs, Gemma jobs, and feedback submission.
- [`app/pipeline/`](app/pipeline/) implements PDF parsing, feature construction, embedding preprocessing, AttentionMIL model loading, and response assembly.
- [`app/services/`](app/services/) coordinates Slurm/Aquifer execution and owns the in-memory job store.
- [`app/clients/`](app/clients/) contains the active Slurm, Aquifer embedding, and Aquifer LLM clients. 
- [`app/database/`](app/database/), [`app/models/`](app/models/), and [`app/repositories/`](app/repositories/) implement SQLite persistence for model configuration and user feedback.
- [`assets/models/`](assets/models/) contains two Qwen-embedding AttentionMIL model packages and the Gemma LoRA adapter.
- [`slurmBackend/`](slurmBackend/README.md) implements remote GPU execution.

## API behaviour

The frontend uses these routes:

- `GET /api/` reports backend availability.
- `POST /api/cases/upload` accepts a PDF and returns extracted `summary`, `research`, and `impact` text.
- `GET /api/analysis/models` returns model configurations seeded into SQLite.
- `GET /api/analysis/runtime-models` reports the configured Aquifer models and Slurm allowlists.
- `POST /api/analysis/jobs` and `GET /api/analysis/jobs/{job_id}` submit and poll MIL inference.
- `POST /api/analysis/llm-feedback/jobs` and its matching `GET` route submit and poll AI insights.
- `POST /api/gemma/jobs` and `GET /api/gemma/jobs/{job_id}` submit and poll the fine-tuned Gemma assessment.
- `POST /api/feedback/` validates and stores the feedback form.

The job routes require the browser-generated `X-User-ID` header. [`app/services/job_store.py`](app/services/job_store.py) checks job ownership and retains completed in-memory jobs for one hour.

## MIL pipeline

[`app/pipeline/manager.py`](app/pipeline/manager.py) resolves the selected database configuration, builds case-level features and spaCy entities, prepares sentence inputs, obtains embeddings, and invokes [`app/pipeline/model_runner.py`](app/pipeline/model_runner.py). The response includes the score/label, sentence attention, heatmap data, features, entity values, feature gates, contribution values, and model metadata.

Embedding pickle output is disabled by `SAVE_EMBEDDINGS_PICKLE = False`. MIL requests are logged to `../logs-users/<user-id>/inferences.jsonl`; the full inference response is not written to SQLite.

## External inference services

[`app/services/embedding_service.py`](app/services/embedding_service.py) tries Slurm and falls back to [`app/clients/aquifer_embedding_client.py`](app/clients/aquifer_embedding_client.py) when the remote result fails validation or raises an exception.

[`app/services/llm_service.py`](app/services/llm_service.py) follows the same Slurm-first pattern for AI insights and falls back to [`app/clients/aquifer_llm_client.py`](app/clients/aquifer_llm_client.py). Gemma is separate: [`app/services/gemma_service.py`](app/services/gemma_service.py) dispatches only through Slurm and validates a GPA from 0 to 4 plus diagnostic comments.

## Database

[`app/database/session.py`](app/database/session.py) fixes the database path at `backend/database.db`. On first startup, [`app/database/init_db.py`](app/database/init_db.py) creates tables and [`app/database/seed_models.py`](app/database/seed_models.py) discovers `assets/models/**/model_config.json`, resolves checkpoints/scalers, and seeds feature importances. If the database file already exists, startup does not reseed it.

The current SQLAlchemy tables are `model_configs` and `feedback`.
