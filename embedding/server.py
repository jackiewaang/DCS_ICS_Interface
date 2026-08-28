# Hosts the embedding model behind a minimal FastAPI text-to-vector service.

import os
import torch
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-4B")

model: SentenceTransformer | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    is_qwen = "qwen" in MODEL_NAME.lower()

    model = SentenceTransformer(
        MODEL_NAME,
        device="cuda",
        model_kwargs={"torch_dtype": torch.float16},
        token=os.getenv("HF_TOKEN") if is_qwen else None,
        trust_remote_code=is_qwen
    )
    
    yield

    model = None

app = FastAPI(lifespan=lifespan)

class EmbeddingRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    prompt: str | None = None # classification prompt to use for embedding

class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]

@app.get("/health")
def health():
    return {
        "status": "ok" if model is not None else "unavailable", 
        "model": MODEL_NAME,
        "model_loaded": model is not None
    }

@app.post("/embed", response_model=EmbeddingResponse)
def embed(request: EmbeddingRequest):
    if model is None:
        raise RuntimeError("Model is not loaded yet.")
    
    bs=int(os.getenv("EMBEDDING_BATCH_SIZE", 8))

    embeddings = model.encode(request.texts, prompt=request.prompt, batch_size=bs)

    embeddings = embeddings.astype("float32")
    return EmbeddingResponse(
        embeddings=embeddings.tolist()
    )
