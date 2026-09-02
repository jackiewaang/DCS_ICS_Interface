import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import requests
from dotenv import dotenv_values
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.database import SessionLocal
from app.llm.service import generate_feedback
from app.models.document import DocumentFeatures, DocumentMetadata
from app.models.inference import (
    Attention,
    Inference,
    ModelConfig,
)
from app.pipeline.manager import PipelineManager
from app.repositories.model_config_repository import get_global_importance
from app.retention import user_analysis_expiry
from slurmBackend.models import SLURM_EMBEDDING_MODELS, SLURM_LLM_MODELS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])
pipeline_manager = PipelineManager()
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


@router.post("/inference")
async def run_inference(
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
    section_payload = sections.model_dump()
    output = pipeline_manager.run_inference(
        section_payload,
        config_id=config_id,
        embedding_model_name=embedding_model_name,
    )
    output["global_importance"] = get_global_importance(
        config_id=config_id,
        feature_names=output.get("feature_names", []),
    )
    _log_inference(user_id, config_id, sections, output["score"])
    output["llm_input"] = _build_llm_input(sections, output, llm_model_name)

    return output


@router.post("/llm-feedback")
async def run_llm_feedback(
    llm_input: LLMInput,
    user_id: UUID = Header(alias="X-User-ID"),
):
    if not (LOGS_DIR / str(user_id)).is_dir():
        raise HTTPException(
            status_code=403,
            detail="Run MIL inference before requesting LLM feedback.",
        )

    model_name = _select_slurm_model(
        llm_input.model_name, SLURM_LLM_MODELS, "LLM"
    )
    payload = llm_input.model_dump()
    payload["model_name"] = model_name

    try:
        return await generate_feedback(payload)
    except Exception as exc:
        logger.exception("LLM feedback generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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


def _save_inference_output(
    config_id: int,
    sections: InferenceSections,
    output: dict,
) -> dict:
    title = _normalise_title(sections.title)
    features = output.get("features") or {}
    entities = output.get("entities") or {}
    sentences = output.get("sentences") or []
    attention = output.get("attention") or []
    feature_names = output.get("feature_names") or []
    feature_gates = output.get("feature_gates") or []
    feature_attributions = {
        name: value
        for name, value in zip(feature_names, feature_gates)
    }

    with SessionLocal() as db:
        document = DocumentMetadata(
            title=title,
            institution=sections.institution,
            uoa=sections.uoa,
            raw_text="\n\n".join(
                section
                for section in (sections.summary, sections.research, sections.impact)
                if section
            ),
            summary_text=sections.summary,
            research_text=sections.research,
            impact_text=sections.impact,
            expires_at=user_analysis_expiry(),
            features=DocumentFeatures(
                features_json=json.dumps(features),
                entities_json=json.dumps(entities),
            ),
        )
        db.add(document)
        db.flush()

        inference = Inference(
            document_id=document.document_id,
            config_id=config_id,
            score=output.get("score"),
            true_label=None,
            prediction_label=output.get("label"),
            narrative_contribution=output.get("narrative_contribution"),
            feature_contribution=output.get("feature_contribution"),
            feature_attributions=json.dumps(feature_attributions),
        )
        db.add(inference)
        db.flush()

        db.add_all(
            [
                Attention(
                    inference_id=inference.inference_id,
                    sentence_text=sentence,
                    weight=weight,
                )
                for sentence, weight in zip(sentences, attention)
            ]
        )

        db.commit()
        return {
            "document_id": document.document_id,
            "inference_id": inference.inference_id,
            "title": title,
            "created_at": inference.created_at.isoformat() if inference.created_at else None,
        }


def _normalise_title(value: str | None) -> str:
    title = (value or "").strip()
    return title or "Untitled inference"
