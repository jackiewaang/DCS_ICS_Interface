import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.endpoints.analysis import router as analysis_router
from app.api.endpoints.cases import router as cases_router
from app.api.endpoints.feedback import router as feedback_router

from app.database import init_db
from app.config.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting backend and checking database...")
    init_db()
    yield
    logger.info("Backend shutdown complete")

app = FastAPI(
    title="REF Impact Analysis Backend API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases_router)
app.include_router(analysis_router)
app.include_router(feedback_router)

@app.get("/api/")
def read_root():
    return {
        "project": "The Language of REF",
        "status": "online"
    }
