import json

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.document import DocumentMetadata
from app.models.inference import Attention, Inference, ModelConfig, ModelFeatureImportance
from app.pipeline.document_extractor import document_extractor

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("/")
def search_cases(q: str = None, uoa: str = None):
    with SessionLocal() as db:
        stmt = (
            select(
                Inference.inference_id,
                DocumentMetadata.document_id,
                DocumentMetadata.case_id,
                DocumentMetadata.title,
                DocumentMetadata.institution,
                DocumentMetadata.uoa,
                DocumentMetadata.gpa,
                Inference.score.label("model_prediction"),
                Inference.prediction_label.label("model_label"),
                Inference.true_label.label("true_label"),
                Inference.created_at,
                ModelConfig.name.label("model_name"),
            )
            .join(DocumentMetadata, Inference.document_id == DocumentMetadata.document_id)
            .join(ModelConfig, Inference.config_id == ModelConfig.config_id)
        )

        if q:
            search = f"%{q}%"
            stmt = stmt.where(
                or_(
                    DocumentMetadata.title.like(search),
                    DocumentMetadata.institution.like(search),
                    cast(DocumentMetadata.document_id, String).like(search),
                    cast(DocumentMetadata.case_id, String).like(search),
                )
            )

        if uoa:
            stmt = stmt.where(DocumentMetadata.uoa == uoa)

        stmt = stmt.order_by(Inference.created_at.desc(), Inference.inference_id.desc())
        return [dict(row) for row in db.execute(stmt).mappings().all()]


@router.get("/latest")
def read_latest_inference():
    data = _get_latest_inference_details()
    if not data:
        raise HTTPException(status_code=404, detail="No analysis results found")
    return data


@router.get("/inference/{inference_id}")
def read_inference(inference_id: int):
    data = _get_inference_details(inference_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return data


@router.post("/upload")
async def upload_case(file: UploadFile = File(...)):
    filename = file.filename or "Untitled case"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty")

    try:
        raw_text = document_extractor.extract_pdf_text(pdf_bytes)
        sections = document_extractor.split_ref_sections(raw_text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not extract PDF text: {exc}") from exc

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in PDF")

    if not any(sections.values()):
        raise HTTPException(status_code=400, detail="Could not identify REF sections in PDF")

    return {
        "title": filename,
        "sections": sections
    }

    # draft = create_draft_case(filename=filename, sections=sections, raw_text=raw_text)

    # return {
    #     "status": "draft",
    #     "document_id": draft["document_id"],
    #     "title": draft["title"],
    #     "sections": draft["sections"],
    # }


@router.get("/{document_id}")
def read_case(document_id: int):
    case = _get_case_by_id(document_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case study not found")
    return case


def _get_inference_details(inference_id: int) -> dict | None:
    with SessionLocal() as db:
        inference = db.scalar(
            select(Inference)
            .options(
                joinedload(Inference.document).joinedload(DocumentMetadata.features),
                joinedload(Inference.model_config),
            )
            .where(Inference.inference_id == inference_id)
        )

        if not inference:
            return None

        case = _document_payload(inference.document)
        case.update(_inference_payload(inference))
        case["heatmap"] = _get_heatmap_for_inference(inference_id)
        return _parse_feature_blobs(case)


def _get_latest_inference_details() -> dict | None:
    with SessionLocal() as db:
        inference = db.scalar(
            select(Inference)
            .options(
                joinedload(Inference.document).joinedload(DocumentMetadata.features),
                joinedload(Inference.model_config),
            )
            .order_by(Inference.created_at.desc(), Inference.inference_id.desc())
            .limit(1)
        )

        if not inference:
            return None

        case = _document_payload(inference.document)
        case.update(_inference_payload(inference))
        case["heatmap"] = _get_heatmap_for_inference(inference.inference_id)
        return _parse_feature_blobs(case)


def _get_case_by_id(document_id: int) -> dict | None:
    with SessionLocal() as db:
        inference = db.scalar(
            select(Inference)
            .options(
                joinedload(Inference.document).joinedload(DocumentMetadata.features),
                joinedload(Inference.model_config),
            )
            .where(Inference.document_id == document_id)
            .order_by(Inference.created_at.desc(), Inference.inference_id.desc())
            .limit(1)
        )

        if inference:
            case = _document_payload(inference.document)
            case.update(_inference_payload(inference))
            case["heatmap"] = _get_heatmap_for_inference(inference.inference_id)
            return _parse_feature_blobs(case)

        document = db.scalar(
            select(DocumentMetadata)
            .options(joinedload(DocumentMetadata.features))
            .where(DocumentMetadata.document_id == document_id)
        )

        if not document:
            return None

        case = _document_payload(document)
        case.update(
            {
                "inference_id": None,
                "model_prediction": None,
                "model_label": None,
                "true_label": None,
                "created_at": None,
                "model_name": None,
                "feature_attributions": {},
                "narrative_contribution": None,
                "feature_contribution": None,
                "heatmap": [],
            }
        )
        return _parse_feature_blobs(case)


def _document_payload(document: DocumentMetadata) -> dict:
    features = document.features
    return {
        "document_id": document.document_id,
        "case_id": document.case_id,
        "title": document.title,
        "institution": document.institution,
        "uoa": document.uoa,
        "status": document.status,
        "ref_year": document.ref_year,
        "gpa": document.gpa,
        "impact_label": document.impact_label,
        "raw_text": document.raw_text,
        "sections": {
            "summary": document.summary_text or "",
            "research": document.research_text or "",
            "impact": document.impact_text or "",
        },
        "features_json": features.features_json if features else None,
        "entities_json": features.entities_json if features else None,
    }


def _inference_payload(inference: Inference) -> dict:
    config_id = inference.config_id
    return {
        "inference_id": inference.inference_id,
        "model_prediction": inference.score,
        "model_label": inference.prediction_label,
        "true_label": inference.true_label,
        "created_at": inference.created_at.isoformat() if inference.created_at else None,
        "model_name": inference.model_config.name if inference.model_config else None,
        "narrative_contribution": inference.narrative_contribution,
        "feature_contribution": inference.feature_contribution,
        "feature_attributions": _json_loads(inference.feature_attributions, default={}),
        "global_importance": _get_global_importance(config_id),
    }


def _get_heatmap_for_inference(inference_id: int) -> list[dict]:
    with SessionLocal() as db:
        stmt = (
            select(
                Attention.sentence_text,
                Attention.weight.label("attention_score"),
            )
            .where(Attention.inference_id == inference_id)
            .order_by(Attention.attention_id)
        )
        return [dict(row) for row in db.execute(stmt).mappings().all()]


def _parse_feature_blobs(case: dict) -> dict:
    case["features"] = _json_loads(case.pop("features_json", None), default={})
    case["entities"] = _json_loads(case.pop("entities_json", None), default={})
    return case


def _get_global_importance(config_id: int | None) -> dict[str, float]:
    if config_id is None:
        return {}

    with SessionLocal() as db:
        rows = db.scalars(
            select(ModelFeatureImportance).where(
                ModelFeatureImportance.config_id == config_id
            )
        ).all()

    return {
        row.feature_name: row.mean_permutation_importance
        for row in rows
    }


def _json_loads(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
