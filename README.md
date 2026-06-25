# DCS_ICS_Interface

React (Vite) frontend + FastAPI backend for the DCS/ICS interface.

## Prerequisites

- **Node.js**: 18+ (includes `npm`)
- **Python**: 3.10–3.12 recommended

## Project structure

- `frontend/` — React app (Vite dev server)
- `backend/` — FastAPI API server + SQLite DB

## Backend (FastAPI) setup + run

The backend uses a local SQLite database at `backend/app/database.db`.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m app.database
python -m app.services.seed_models

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Backend URLs

- API base: `http://localhost:8001/api`
- Health check: `http://localhost:8001/`
- OpenAPI/Swagger: `http://localhost:8001/docs`

## Frontend (React) setup + run

Open a **second** terminal at the repo root and run:

```bash
cd frontend
npm install
npm run dev
```

Vite will print the dev URL (typically `http://localhost:5173`).

### Optional sample-data mode

If you want to work on the UI without the backend running, set `VITE_USE_SAMPLE_DATA=true` before starting Vite. The frontend will then use the local JSON files in `frontend/public/` as demo data.

You can also override the backend URL with `VITE_API_BASE` if your FastAPI server runs on a different port.

## Running both together (dev)

You should have two terminals running:

- **Terminal A**: FastAPI on `http://localhost:8001`
- **Terminal B**: Vite on `http://localhost:5173`

The frontend is configured to call the backend at `http://localhost:8001/api`.