import json

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.database import SessionLocal
from app.models.document import DocumentFeatures, DocumentMetadata
from app.models.inference import Attention, Inference, ModelConfig, ModelFeatureImportance
from app.pipeline.manager import PipelineManager

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])
pipeline_manager = PipelineManager()


class InferenceSections(BaseModel):
    title: str = "Manual inference"
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
async def run_inference(config_id: int, sections: InferenceSections):
    section_payload = sections.model_dump()
    output = pipeline_manager.run_inference(
        section_payload,
        config_id=config_id,
    )
    output["global_importance"] = _get_global_importance(
        config_id=config_id,
        feature_names=output.get("feature_names", []),
    )
    output.update(_save_inference_output(
        config_id=config_id,
        sections=sections,
        output=output,
    ))

    return output


def _save_inference_output(
    config_id: int,
    sections: InferenceSections,
    output: dict,
) -> dict:
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
            title=f"[Inference] {sections.title}",
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
            "created_at": inference.created_at.isoformat() if inference.created_at else None,
        }


def _get_global_importance(config_id: int, feature_names: list[str]) -> dict[str, float]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(ModelFeatureImportance).where(
                ModelFeatureImportance.config_id == config_id
            )
        ).all()

    if rows:
        return {
            row.feature_name: row.mean_permutation_importance
            for row in rows
        }

    return {feature_name: 0.0 for feature_name in feature_names}
