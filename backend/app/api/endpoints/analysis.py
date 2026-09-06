import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import requests
from dotenv import dotenv_values
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.database import SessionLocal
from app.clients.aquifer_llm_client import AquiferLLMClient
from app.clients.slurm_client import SlurmClient
from app.models.model_configs import ModelConfig
from app.pipeline.manager import PipelineManager
from app.repositories.model_config_repository import get_global_importance
from app.services.job_store import JobForbidden, JobNotFound, job_store
from app.services.llm_service import LLMService
from slurmBackend.models import SLURM_EMBEDDING_MODELS, SLURM_LLM_MODELS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])
pipeline_manager = PipelineManager()
llm_service = LLMService(
    slurm_client=SlurmClient(),
    aquifer_client=AquiferLLMClient(),
)
REPO_ROOT = Path(__file__).resolve().parents[4]
LOGS_DIR = REPO_ROOT / "logs-users"
ENV_PATH = REPO_ROOT / ".env"

EMBEDDING_HEALTH_URL = os.getenv(
    "AQUIFER_EMBEDDING_HEALTH",
    "http://localhost:8001/health",
)

VLLM_BASE_URL = os.getenv(
    "VLLM_BASE_URL",
    "http://localhost:8002/v1"
).rstrip("/")

RUNTIME_MODEL_LOOKUP_TIMEOUT = 2


class InferenceSections(BaseModel):
    title: str = "Untitled inference"
    institution: str = "Unknown Institution"
    uoa: str = "Unknown UoA"
    summary: str = ""
    research: str = ""
    impact: str = ""


class LLMInput(BaseModel):
    prediction_label: str | None = None
    score: float | None = None
    top_sentences: list[dict] = Field(default_factory=list)
    top_features: list[dict] = Field(default_factory=list)
    summary: str = ""
    details: str = ""
    model_name: str | None = None


@router.get("/runtime-models")
def get_runtime_models():
    embedding_model = _read_env_value(ENV_PATH, "AQUIFER_EMBEDDING_MODEL")
    llm_model = _read_env_value(ENV_PATH, "AQUIFER_LLM_MODEL")

    embedding_source = "environment"
    llm_source = "environment"

    if not embedding_model:
        embedding_model = _get_embedding_endpoint_model()
        embedding_source = "service" if embedding_model else "unavailable"

    if not llm_model:
        llm_model = _get_llm_endpoint_model()
        llm_source = "service" if llm_model else "unavailable"

    return {
        "embedding_model": embedding_model,
        "embedding_source": embedding_source,
        "llm_model": llm_model,
        "llm_source": llm_source,
        "slurm_embedding_models": SLURM_EMBEDDING_MODELS,
        "slurm_llm_models": SLURM_LLM_MODELS,
    }


@router.get("/models")
def list_models():
    with SessionLocal() as db:
        models = db.scalars(
            select(ModelConfig).order_by(ModelConfig.config_id)
        ).all()

        return [
            {
                column.name: getattr(model, column.name)
                for column in ModelConfig.__table__.columns
            }
            for model in models
        ]


def _read_env_value(env_path: Path, key: str) -> str | None:
    try:
        value = dotenv_values(env_path).get(key)
    except (OSError, ValueError):
        logger.warning("Could not read runtime model environment file: %s", env_path)
        return None

    return value.strip() if isinstance(value, str) and value.strip() else None


def _get_embedding_endpoint_model() -> str | None:
    try:
        response = requests.get(
            EMBEDDING_HEALTH_URL,
            timeout=RUNTIME_MODEL_LOOKUP_TIMEOUT,
        )
        response.raise_for_status()
        model = response.json().get("model")
        return model.strip() if isinstance(model, str) and model.strip() else None
    except (requests.RequestException, ValueError, TypeError):
        logger.warning("Could not retrieve the embedding model from %s", EMBEDDING_HEALTH_URL)
        return None


def _get_llm_endpoint_model() -> str | None:
    try:
        response = requests.get(
            f"{VLLM_BASE_URL}/models",
            timeout=RUNTIME_MODEL_LOOKUP_TIMEOUT,
        )
        response.raise_for_status()
        models = response.json().get("data") or []
        model = models[0].get("id") if models else None
        return model.strip() if isinstance(model, str) and model.strip() else None
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        logger.warning("Could not retrieve the LLM model from %s/models", VLLM_BASE_URL)
        return None


@router.post("/jobs", status_code=202)
async def submit_inference_job(
    config_id: int,
    sections: InferenceSections,
    embedding_model_name: str | None = None,
    llm_model_name: str | None = None,
    user_id: UUID = Header(alias="X-User-ID"),
):
    embedding_model_name = _select_slurm_model(
        embedding_model_name, SLURM_EMBEDDING_MODELS, "embedding"
    )
    llm_model_name = _select_slurm_model(llm_model_name, SLURM_LLM_MODELS, "LLM")
    request_id = str(uuid4())
    job_id = job_store.submit(
        str(user_id),
        lambda: _run_inference_job(
            request_id=request_id,
            user_id=user_id,
            config_id=config_id,
            sections=sections,
            embedding_model_name=embedding_model_name,
            llm_model_name=llm_model_name,
        ),
    )
    logger.info(
        "MIL inference job accepted request_id=%s job_id=%s user_id=%s",
        request_id,
        job_id,
        user_id,
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}")
async def get_inference_job(
    job_id: str,
    user_id: UUID = Header(alias="X-User-ID"),
):
    return _get_job_response(job_id, user_id)


async def _run_inference_job(
    request_id: str,
    user_id: UUID,
    config_id: int,
    sections: InferenceSections,
    embedding_model_name: str,
    llm_model_name: str,
) -> dict:
    started_at = time.monotonic()
    try:
        output = await asyncio.to_thread(
            pipeline_manager.run_inference,
            sections.model_dump(),
            config_id=config_id,
            embedding_model_name=embedding_model_name,
        )
        output["global_importance"] = get_global_importance(
            config_id=config_id,
            feature_names=output.get("feature_names", []),
        )
        _log_inference(user_id, config_id, sections, output["score"])
        output["llm_input"] = _build_llm_input(sections, output, llm_model_name)
        logger.info(
            "MIL inference job completed request_id=%s elapsed_seconds=%.2f",
            request_id,
            time.monotonic() - started_at,
        )
        return output
    except Exception:
        logger.exception(
            "MIL inference job failed request_id=%s elapsed_seconds=%.2f",
            request_id,
            time.monotonic() - started_at,
        )
        raise


@router.post("/llm-feedback/jobs", status_code=202)
async def submit_llm_feedback_job(
    llm_input: LLMInput,
    user_id: UUID = Header(alias="X-User-ID"),
):
    request_id = str(uuid4())
    logger.info(
        "LLM feedback request started request_id=%s user_id=%s requested_model=%s",
        request_id,
        user_id,
        llm_input.model_name,
    )

    if not (LOGS_DIR / str(user_id)).is_dir():
        logger.warning(
            "LLM feedback request rejected request_id=%s reason=missing_inference_log",
            request_id,
        )
        raise HTTPException(
            status_code=403,
            detail="Run MIL inference before requesting LLM feedback.",
        )

    model_name = _select_slurm_model(
        llm_input.model_name, SLURM_LLM_MODELS, "LLM"
    )
    payload = llm_input.model_dump()
    payload["model_name"] = model_name

    job_id = job_store.submit(
        str(user_id),
        lambda: _run_llm_feedback_job(request_id, payload, model_name),
    )
    logger.info(
        "LLM feedback job accepted request_id=%s job_id=%s",
        request_id,
        job_id,
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/llm-feedback/jobs/{job_id}")
async def get_llm_feedback_job(
    job_id: str,
    user_id: UUID = Header(alias="X-User-ID"),
):
    return _get_job_response(job_id, user_id)


async def _run_llm_feedback_job(
    request_id: str,
    payload: dict,
    model_name: str,
) -> dict:
    started_at = time.monotonic()
    try:
        result = await llm_service.generate_feedback(payload, request_id=request_id)
        logger.info(
            "LLM feedback job completed request_id=%s model=%s elapsed_seconds=%.2f",
            request_id,
            model_name,
            time.monotonic() - started_at,
        )
        return result
    except Exception as exc:
        logger.exception(
            "LLM feedback job failed request_id=%s model=%s elapsed_seconds=%.2f error_type=%s",
            request_id,
            model_name,
            time.monotonic() - started_at,
            type(exc).__name__,
        )
        raise


def _get_job_response(job_id: str, user_id: UUID) -> dict:
    try:
        job = job_store.get(job_id, str(user_id))
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail="Inference job not found.") from exc
    except JobForbidden as exc:
        raise HTTPException(status_code=403, detail="This inference job belongs to another user.") from exc

    response = {"job_id": job_id, "status": job.status}
    if job.status == "completed":
        response["result"] = job.result
    elif job.status == "failed":
        response["error"] = job.error
    return response


def _log_inference(
    user_id: UUID,
    config_id: int,
    sections: InferenceSections,
    score: float,
) -> None:
    user_dir = LOGS_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_id": config_id,
        "inputs": {
            "summary": sections.summary,
            "research": sections.research,
            "impact": sections.impact,
        },
        "output": {"prediction_score": score},
    }
    with (user_dir / "inferences.jsonl").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _build_llm_input(
    sections: InferenceSections,
    output: dict,
    llm_model_name: str,
) -> dict:
    top_sentences = sorted(
        (
            {"sentence_text": sentence, "weight": weight}
            for sentence, weight in zip(
                output.get("sentences") or [],
                output.get("attention") or [],
            )
        ),
        key=lambda item: item["weight"],
        reverse=True,
    )[:10]

    features = output.get("features") or {}
    top_features = sorted(
        (
            {
                "feature_name": name,
                "local_weight": weight,
                "value": features[name],
            }
            for name, weight in zip(
                output.get("feature_names") or [],
                output.get("feature_gates") or [],
            )
            if name in features
        ),
        key=lambda item: item["local_weight"],
        reverse=True,
    )[:10]

    return {
        "prediction_label": output.get("label"),
        "score": output.get("score"),
        "top_sentences": top_sentences,
        "top_features": top_features,
        "summary": sections.summary,
        "details": sections.impact,
        "model_name": llm_model_name,
    }


def _validate_slurm_model(model_name: str, allowed_models: list[str], kind: str) -> None:
    if model_name not in allowed_models:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported Slurm {kind} model: {model_name}",
        )


def _select_slurm_model(
    requested_model: str | None,
    allowed_models: list[str],
    kind: str,
) -> str:
    if not allowed_models:
        raise HTTPException(
            status_code=503,
            detail=f"No Slurm {kind} models are configured.",
        )
    model_name = requested_model or allowed_models[0]
    _validate_slurm_model(model_name, allowed_models, kind)
    return model_name
