from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.analyse import router as analysis_router
from app.api.cases import router as cases_router
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
app.include_router(cases_router)
app.include_router(analysis_router)

@app.get("/")
def read_root():
    return {
        "project": "The Language of REF",
        "status": "online"
    }