import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.database import SessionLocal
from app.llm.service import generate_review
from app.models.document import DocumentFeatures, DocumentMetadata
from app.models.inference import (
    Attention,
    Inference,
    LLMInference,
    LLMInferenceStatus,
    ModelConfig,
)
from app.pipeline.manager import PipelineManager
from app.repositories.model_config_repository import get_global_importance
from app.retention import user_analysis_expiry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])
pipeline_manager = PipelineManager()
LOGS_DIR = Path(__file__).resolve().parents[4] / "logs-users"


class InferenceSections(BaseModel):
    title: str = "Untitled inference"
    institution: str = "Unknown Institution"
    uoa: str = "Unknown UoA"
    summary: str = ""
    research: str = ""
    impact: str = ""


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


@router.post("/inference")
async def run_inference(
    config_id: int,
    sections: InferenceSections,
    user_id: UUID = Header(alias="X-User-ID"),
):
    section_payload = sections.model_dump()
    output = pipeline_manager.run_inference(
        section_payload,
        config_id=config_id,
    )
    output["global_importance"] = get_global_importance(
        config_id=config_id,
        feature_names=output.get("feature_names", []),
    )
    _log_inference(user_id, config_id, sections, output["score"])
    output.update(_save_inference_output(
        config_id=config_id,
        sections=sections,
        output=output,
    ))
    _create_llm_inference(output["inference_id"])
    asyncio.create_task(_run_llm_review(output["inference_id"]))

    return output


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


@router.get("/llm-inference/{inference_id}")
def get_llm_inference(inference_id: int):
    with SessionLocal() as db:
        llm_inference = db.scalar(
            select(LLMInference).where(LLMInference.inference_id == inference_id)
        )

        if llm_inference is None:
            raise HTTPException(status_code=404, detail="LLM inference result not found")

        status = _status_value(llm_inference.status)
        if status == LLMInferenceStatus.ERROR.value:
            return {
                "inference_id": inference_id,
                "status": status,
                "error_message": llm_inference.error_message,
            }

        if status == LLMInferenceStatus.COMPLETED.value:
            return {
                "inference_id": inference_id,
                "status": status,
                "significance_limitations": _json_loads(
                    llm_inference.significance_limitations,
                    default=[],
                ),
                "significance_improvements": _json_loads(
                    llm_inference.significance_improvements,
                    default=[],
                ),
                "outreach_limitations": _json_loads(
                    llm_inference.outreach_limitations,
                    default=[],
                ),
                "outreach_improvements": _json_loads(
                    llm_inference.outreach_improvements,
                    default=[],
                ),
            }

        return {
            "inference_id": inference_id,
            "status": status,
        }


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


def _create_llm_inference(inference_id: int) -> None:
    with SessionLocal() as db:
        db.add(
            LLMInference(
                inference_id=inference_id,
                status=LLMInferenceStatus.RUNNING,
            )
        )
        db.commit()


async def _run_llm_review(inference_id: int) -> None:
    try:
        await generate_review(inference_id)
    except Exception:
        logger.exception("LLM review failed: inference_id=%s", inference_id)


def _normalise_title(value: str | None) -> str:
    title = (value or "").strip()
    return title or "Untitled inference"


def _status_value(status: LLMInferenceStatus | str) -> str:
    return status.value if isinstance(status, LLMInferenceStatus) else status


def _json_loads(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
