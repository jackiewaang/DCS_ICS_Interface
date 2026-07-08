import json

from sqlalchemy import cast, or_, select, String
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models.document import DocumentFeatures, DocumentMetadata
from app.models.inference import Attention, Inference, ModelConfig

GTF_ORDER = [
    "Flesch Reading Ease", "Dale-Chall Readability Score", "SMOG Index", "Automated Readability Index",
    "Sentiment (mean)", "Sentiment (10th)", "Sentiment (50th)", "Sentiment (75th)", "Sentiment (90th)",
    "Number of organizations mentioned", "Number of named individuals", "Number of countries or regions mentioned",
    "Word count", "Paragraph count",
    'PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT',
    'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY',
    'QUANTITY', 'ORDINAL', 'CARDINAL'
]


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


def _parse_feature_blobs(case_dict: dict) -> dict:
    case_dict["features"] = json.loads(case_dict.get("features_json") or "{}")
    case_dict["entities"] = json.loads(case_dict.get("entities_json") or "{}")
    return case_dict


def get_cases(search_query: str = None, uoa: str = None):
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
                ModelConfig.name.label("model_name"),
            )
            .join(DocumentMetadata, Inference.document_id == DocumentMetadata.document_id)
            .join(ModelConfig, Inference.config_id == ModelConfig.config_id)
        )

        if search_query:
            search = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    DocumentMetadata.title.like(search),
                    DocumentMetadata.institution.like(search),
                    cast(DocumentMetadata.document_id, String).like(search),
                )
            )

        if uoa:
            stmt = stmt.where(DocumentMetadata.uoa == uoa)

        stmt = stmt.order_by(Inference.inference_id.desc())
        return [dict(row) for row in db.execute(stmt).mappings().all()]


def get_inference_details(inference_id: int):
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

        case_dict = _document_payload(inference.document)
        case_dict.update(
            {
                "inference_id": inference.inference_id,
                "model_prediction": inference.score,
                "model_label": inference.prediction_label,
                "true_label": inference.true_label,
                "model_name": inference.model_config.name,
                "input_granularity": inference.model_config.input_granularity,
            }
        )
        _parse_feature_blobs(case_dict)
        case_dict["heatmap"] = get_heatmap_for_inference(inference_id)
        return case_dict


def get_heatmap_for_inference(inference_id: int):
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


def get_case_by_id(document_id: int):
    with SessionLocal() as db:
        inference = db.scalar(
            select(Inference)
            .options(
                joinedload(Inference.document).joinedload(DocumentMetadata.features),
                joinedload(Inference.model_config),
            )
            .where(Inference.document_id == document_id)
            .order_by(Inference.inference_id.desc())
            .limit(1)
        )

        if inference:
            case_dict = _document_payload(inference.document)
            case_dict.update(
                {
                    "inference_id": inference.inference_id,
                    "model_prediction": inference.score,
                    "model_label": inference.prediction_label,
                    "true_label": inference.true_label,
                    "model_name": inference.model_config.name,
                }
            )
            _parse_feature_blobs(case_dict)
            case_dict["heatmap"] = get_heatmap_for_inference(inference.inference_id)
            return case_dict

        document = db.scalar(
            select(DocumentMetadata)
            .options(joinedload(DocumentMetadata.features))
            .where(DocumentMetadata.document_id == document_id)
        )

        if not document:
            return None

        case_dict = _document_payload(document)
        case_dict.update(
            {
                "inference_id": None,
                "model_prediction": None,
                "model_label": None,
                "true_label": None,
                "model_name": None,
                "heatmap": [],
            }
        )
        return _parse_feature_blobs(case_dict)


def create_inference_case(filename, features, sentences, prediction, institution, uoa, config_id):
    """
    Saves new inference data into the database.
    Leaves case_id, ref_year, gpa, and impact_label as NULL for new inferences.
    """
    with SessionLocal() as db:
        try:
            entities_blob = json.dumps(features.get("highlights", {}))
            stats_only = {k: v for k, v in features.items() if k != "highlights"}
            features_blob = json.dumps(stats_only)

            document = DocumentMetadata(
                title=f"[Inference] {filename}",
                institution=institution,
                uoa=uoa,
                raw_text="\n\n".join(sentences),
                features=DocumentFeatures(
                    features_json=features_blob,
                    entities_json=entities_blob,
                ),
            )
            db.add(document)
            db.flush()

            gates = prediction.get("feature_gates", [])
            attr_dict = {name: val for name, val in zip(GTF_ORDER, gates)}

            inference = Inference(
                document_id=document.document_id,
                config_id=config_id,
                score=prediction["score"],
                prediction_label=prediction["label"],
                true_label=None,
                narrative_contribution=prediction["narrative_contribution"],
                feature_contribution=prediction["feature_contribution"],
                feature_attributions=json.dumps(attr_dict),
            )
            db.add(inference)
            db.flush()

            att_data = prediction.get("attention")
            if att_data and len(att_data) > 0:
                db.add_all(
                    [
                        Attention(
                            inference_id=inference.inference_id,
                            sentence_text=sent,
                            weight=weight,
                        )
                        for sent, weight in zip(sentences, att_data)
                    ]
                )
                print(f"--- INFO: Saved {len(att_data)} sentences to Heatmap ---")

            db.commit()
            return document.document_id
        except Exception as e:
            db.rollback()
            print(f"DATABASE CRITICAL ERROR: {e}")
            raise
