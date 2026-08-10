import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.document import DocumentMetadata
from app.models.inference import Attention, Inference, ModelConfig, ModelFeatureImportance


BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODELS_ROOT = BACKEND_ROOT / "assets" / "models"

CASE_FEATURE_ATTENTION_TEST = "case_feature_attention_test.csv"
FEATURE_VALIDATION_SUMMARY = "feature_validation_summary.csv"
SENTENCE_ATTENTION_TEST = "sentence_attention_test.csv"
ATTRIBUTION_SUFFIX = "_AbsAttribution"
SUPPORTED_REF_YEARS = {2014, 2021}


def seed_inferences(
    db: Session | None = None,
    models_root: Path = MODELS_ROOT,
    ref_year: int | None = None,
) -> dict[str, int]:
    """
    Seed model-level importances, case predictions, branch contributions, and sentence attention.

    Model configs and past cases should already exist in the database. Missing model configs
    or case IDs are skipped so this can be run against partially populated assets.
    When ref_year is provided, only documents from that REF year receive inferences.
    """
    owns_session = db is None
    db = db or SessionLocal()

    try:
        selected_ref_year = _normalise_ref_year(ref_year) if ref_year is not None else None
        totals = {
            "models": 0,
            "feature_importances": 0,
            "inferences": 0,
            "attentions": 0,
            "missing_documents": 0,
        }

        for model_dir in sorted(path for path in models_root.iterdir() if path.is_dir()):
            model_config = _get_model_config(db, model_dir)
            if model_config is None:
                print(f"Skipping {model_dir.name}: model config is not seeded.")
                continue

            totals["models"] += 1
            totals["feature_importances"] += _seed_feature_importances(
                db,
                model_config,
                model_dir / FEATURE_VALIDATION_SUMMARY,
            )

            inference_by_case_id, missing_documents = _seed_case_predictions(
                db,
                model_config,
                model_dir,
                ref_year=selected_ref_year,
            )
            totals["inferences"] += len(inference_by_case_id)
            totals["missing_documents"] += missing_documents
            totals["attentions"] += _seed_sentence_attentions(
                db,
                model_dir,
                inference_by_case_id,
            )

        if owns_session:
            db.commit()

        return totals
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()


def seed_ref2014_inferences(db: Session | None = None) -> dict[str, int]:
    return seed_inferences(db=db, ref_year=2014)


def seed_ref2021_inferences(db: Session | None = None) -> dict[str, int]:
    return seed_inferences(db=db, ref_year=2021)


def _get_model_config(db: Session, model_dir: Path) -> ModelConfig | None:
    config_name = _model_name(model_dir)
    if not config_name:
        return None

    return db.scalar(select(ModelConfig).where(ModelConfig.name == config_name))


def _model_name(model_dir: Path) -> str | None:
    config_path = model_dir / "model_config.json"
    if not config_path.exists():
        return model_dir.name

    with config_path.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    return config.get("name") or model_dir.name


def _seed_feature_importances(
    db: Session,
    model_config: ModelConfig,
    importance_path: Path,
) -> int:
    if not importance_path.exists():
        print(f"Missing feature validation summary: {importance_path}")
        return 0

    existing_rows = {
        row.feature_name: row
        for row in db.scalars(
            select(ModelFeatureImportance).where(
                ModelFeatureImportance.config_id == model_config.config_id
            )
        )
    }

    seeded_count = 0
    with importance_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            feature_name = _clean_string(row.get("Feature"))
            if not feature_name:
                continue

            importance = _safe_float(row.get("MeanPermutationImportance"), default=0.0)
            existing_row = existing_rows.get(feature_name)
            if existing_row is None:
                existing_rows[feature_name] = ModelFeatureImportance(
                    config_id=model_config.config_id,
                    feature_name=feature_name,
                    mean_permutation_importance=importance or 0.0,
                )
                db.add(existing_rows[feature_name])
            else:
                existing_row.mean_permutation_importance = importance or 0.0
            seeded_count += 1

    return seeded_count


def _seed_case_predictions(
    db: Session,
    model_config: ModelConfig,
    model_dir: Path,
    ref_year: int | None = None,
) -> tuple[dict[str, Inference], int]:
    inference_by_case_id: dict[str, Inference] = {}
    missing_documents = 0

    for case_path in _case_prediction_paths(model_dir):
        with case_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            for row in csv.DictReader(csv_file):
                case_id = _normalise_case_id(row.get("Case ID"))
                if not case_id:
                    continue

                document_stmt = select(DocumentMetadata).where(
                    DocumentMetadata.case_id == case_id
                )
                if ref_year is not None:
                    document_stmt = document_stmt.where(DocumentMetadata.ref_year == ref_year)

                document = db.scalar(document_stmt)
                if document is None:
                    missing_documents += 1
                    continue

                inference = _get_or_create_inference(db, model_config, document)
                inference.score = _safe_float(row.get("Prediction"), default=None)
                inference.true_label = _safe_float(row.get("Label"), default=None)
                inference.prediction_label = _prediction_label(inference.score)

                if hasattr(inference, "narrative_contribution"):
                    inference.narrative_contribution = _safe_float(
                        row.get("LLM_Branch_Contribution"),
                        default=None,
                    )
                if hasattr(inference, "feature_contribution"):
                    inference.feature_contribution = _safe_float(
                        row.get("Handcrafted_Branch_Contribution"),
                        default=None,
                    )
                if hasattr(inference, "feature_attributions"):
                    inference.feature_attributions = json.dumps(
                        _feature_attributions_from_row(row)
                    )

                inference_by_case_id[case_id] = inference

    return inference_by_case_id, missing_documents


def _case_prediction_paths(model_dir: Path) -> list[Path]:
    exact_path = model_dir / CASE_FEATURE_ATTENTION_TEST
    fold_paths = sorted(model_dir.glob("case_feature_attention_fold_*.csv"))
    if fold_paths:
        return fold_paths
    return [exact_path] if exact_path.exists() else []


def _get_or_create_inference(
    db: Session,
    model_config: ModelConfig,
    document: DocumentMetadata,
) -> Inference:
    inference = db.scalar(
        select(Inference).where(
            Inference.config_id == model_config.config_id,
            Inference.document_id == document.document_id,
        )
    )
    if inference is not None:
        return inference

    inference = Inference(
        config_id=model_config.config_id,
        document_id=document.document_id,
    )
    db.add(inference)
    db.flush()
    return inference


def _seed_sentence_attentions(
    db: Session,
    model_dir: Path,
    inference_by_case_id: dict[str, Inference],
) -> int:
    if not inference_by_case_id:
        return 0

    for inference in inference_by_case_id.values():
        db.execute(delete(Attention).where(Attention.inference_id == inference.inference_id))

    seeded_count = 0
    for sentence_path in _sentence_attention_paths(model_dir):
        with sentence_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            for row in csv.DictReader(csv_file):
                case_id = _normalise_case_id(row.get("Case ID"))
                inference = inference_by_case_id.get(case_id)
                if inference is None:
                    continue

                sentence = _clean_string(row.get("Sentence"))
                weight = _safe_float(
                    row.get("Sentence Attention Weight") or row.get("Attention Weight"),
                    default=None,
                )
                if not sentence or weight is None:
                    continue

                db.add(
                    Attention(
                        inference_id=inference.inference_id,
                        sentence_text=sentence,
                        weight=weight,
                    )
                )
                seeded_count += 1

    return seeded_count


def _sentence_attention_paths(model_dir: Path) -> list[Path]:
    exact_path = model_dir / SENTENCE_ATTENTION_TEST
    fold_paths = sorted(model_dir.glob("sentence_attention_fold_*.csv"))
    if fold_paths:
        return fold_paths
    return [exact_path] if exact_path.exists() else []


def _feature_attributions_from_row(row: dict[str, Any]) -> dict[str, float]:
    attributions: dict[str, float] = {}
    for column, value in row.items():
        if not column.endswith(ATTRIBUTION_SUFFIX):
            continue

        feature_name = column[: -len(ATTRIBUTION_SUFFIX)]
        if not feature_name:
            continue

        attributions[feature_name] = _safe_float(value, default=0.0) or 0.0

    return attributions


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _normalise_ref_year(value: Any) -> int:
    ref_year = _safe_int(value)
    if ref_year not in SUPPORTED_REF_YEARS:
        raise ValueError(f"Unsupported REF year: {value}")
    return ref_year


def _normalise_case_id(value: Any) -> str:
    if value in (None, ""):
        return ""
    numeric_case_id = _safe_int(value)
    if numeric_case_id is not None:
        return str(numeric_case_id)
    return str(value).strip()


def _clean_string(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip() or None


def _prediction_label(score: float | None) -> str | None:
    if score is None:
        return None
    return "High" if score >= 0.5 else "Low"


if __name__ == "__main__":
    result = seed_inferences()
    print(f"Seeded inference assets: {result}")
