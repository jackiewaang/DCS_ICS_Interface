from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints.analysis import router as analysis_router
from app.api.endpoints.cases import router as cases_router
from app.api.endpoints.seeding import router as seeding_router
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Checking database tables...")
    init_db() 
    yield
    print("Shutting down...")

app = FastAPI(
    title="The Language of REF API",
    version="2.0.0",
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
app.include_router(seeding_router)

@app.get("/")
def read_root():
    return {
        "project": "The Language of REF",
        "status": "online"
    }
