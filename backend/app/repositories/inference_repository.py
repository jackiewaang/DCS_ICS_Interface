import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.inference import Attention, Inference, LLMInference, LLMInferenceStatus
from app.models.document import DocumentMetadata


def get_attention_mil_results_for_llm(inference_id: int) -> dict[str, Any] | None:
    with SessionLocal() as db:
        inference = db.scalar(
            select(Inference)
            .options(joinedload(Inference.document).joinedload(DocumentMetadata.features))
            .where(Inference.inference_id == inference_id)
        )

        if inference is None:
            return None

        top_sentences = [
            {
                "sentence_text": attention.sentence_text,
                "weight": attention.weight,
            }
            for attention in db.scalars(
                select(Attention)
                .where(Attention.inference_id == inference_id)
                .order_by(Attention.weight.desc())
                .limit(10)
            ).all()
        ]

        feature_attributions = _json_loads(inference.feature_attributions, default={})
        feature_values = _json_loads(
            inference.document.features.features_json
            if inference.document and inference.document.features
            else None,
            default={},
        )

        top_features = []
        for feature_name, local_weight in sorted(
            feature_attributions.items(),
            key=lambda item: _safe_float(item[1]),
            reverse=True,
        ):
            if feature_name not in feature_values:
                continue

            top_features.append(
                {
                    "feature_name": feature_name,
                    "local_weight": local_weight,
                    "value": feature_values[feature_name],
                }
            )
            if len(top_features) == 10:
                break

        document = inference.document
        return {
            "inference_id": inference.inference_id,
            "prediction_label": inference.prediction_label,
            "score": inference.score,
            "top_sentences": top_sentences,
            "top_features": top_features,
            "summary": document.summary_text if document else "",
            "details": document.impact_text if document else "",
        }


def save_llm_inference_completed(
    inference_id: int,
    significance_limitations: Any,
    significance_improvements: Any,
    outreach_limitations: Any,
    outreach_improvements: Any,
) -> dict[str, Any]:
    with SessionLocal() as db:
        llm_inference = db.scalar(
            select(LLMInference).where(LLMInference.inference_id == inference_id)
        )
        if llm_inference is None:
            raise ValueError(f"LLM inference row for inference {inference_id} was not found.")

        llm_inference.significance_limitations = json.dumps(significance_limitations)
        llm_inference.significance_improvements = json.dumps(significance_improvements)
        llm_inference.outreach_limitations = json.dumps(outreach_limitations)
        llm_inference.outreach_improvements = json.dumps(outreach_improvements)
        llm_inference.status = LLMInferenceStatus.COMPLETED
        llm_inference.error_message = None
        db.commit()

        return {
            "llm_inference_id": llm_inference.llm_inference_id,
            "inference_id": llm_inference.inference_id,
            "status": llm_inference.status.value,
            "significance_limitations": significance_limitations,
            "significance_improvements": significance_improvements,
            "outreach_limitations": outreach_limitations,
            "outreach_improvements": outreach_improvements,
        }


def save_llm_inference_error(inference_id: int, error_message: str) -> dict[str, Any]:
    with SessionLocal() as db:
        llm_inference = db.scalar(
            select(LLMInference).where(LLMInference.inference_id == inference_id)
        )
        if llm_inference is None:
            raise ValueError(f"LLM inference row for inference {inference_id} was not found.")

        llm_inference.status = LLMInferenceStatus.ERROR
        llm_inference.error_message = error_message
        db.commit()

        return {
            "llm_inference_id": llm_inference.llm_inference_id,
            "inference_id": llm_inference.inference_id,
            "status": llm_inference.status.value,
            "error_message": error_message,
        }


def _json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
