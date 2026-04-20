from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import cases, analysis
from app.database import init_db

# Lifespan handles startup and shutdown logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Server starts
    print("Checking database tables...")
    init_db() 
    yield
    # Server shuts down
    print("Shutting down...")

app = FastAPI(
    title="The Language of REF API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers using the new pathing
app.include_router(cases.router, prefix="/cases", tags=["Cases"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])

@app.get("/")
def read_root():
    return {
        "project": "The Language of REF",
        "status": "online"
    }