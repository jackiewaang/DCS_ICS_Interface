import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.document import DocumentMetadata
from app.models.inference import Inference, ModelConfig, ModelFeatureImportance
from app.pipeline.feature_schema import DEFAULT_FEATURE_ORDER


BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODELS_ROOT = BACKEND_ROOT / "assets" / "models"

MODEL_FILE_SUFFIXES = (".pth", ".pt", ".bin", ".safetensors")
SCALER_FILE_SUFFIXES = (".joblib", ".pkl", ".pickle")
FEATURE_VALIDATION_SUMMARY = "feature_validation_summary.csv"
CASE_FEATURE_ATTENTION_TEST = "case_feature_attention_test.csv"
ATTRIBUTION_SUFFIXES = ("_AbsAttribution", "_Attribution")
def seed_models(db: Session | None = None, models_root: Path = MODELS_ROOT) -> int:
    """
    Discover model_config.json files under assets/models and upsert model_configs.

    Returns the number of model configuration rows created or updated.
    """
    owns_session = db is None
    db = db or SessionLocal()

    try:
        seeded_count = 0
        for config_path in sorted(models_root.rglob("model_config.json")):
            model_config = _build_model_config(config_path)
            if model_config is None:
                continue

            db_model_config = _upsert_model_config(db, model_config)
            db.flush()
            _seed_feature_importances(db, db_model_config, config_path.parent)
            seeded_count += 1

        if owns_session:
            db.commit()

        return seeded_count
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()


def _build_model_config(config_path: Path) -> dict[str, Any] | None:
    with config_path.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    model_dir = config_path.parent
    model_path = _configured_path(
        config,
        model_dir,
        ("model_path", "checkpoint_path", "checkpoint"),
    ) or _find_model_path(model_dir)
    if model_path is None:
        print(f"Skipping {model_dir.name}: no model checkpoint found.")
        return None

    scaler_path = _configured_path(
        config,
        model_dir,
        ("scaler_path", "scaler"),
    ) or _find_scaler_path(model_dir)

    return {
        "name": config.get("name") or model_dir.name,
        "emb_model": config.get("emb_model"),
        "run_mode": config.get("run_mode"),
        "fusion_type": config.get("fusion_type") or "gated",
        "normalise_emb": bool(config.get("normalise_emb", False)),
        "normalise_case_feats": bool(config.get("normalise_case_feats", False)),
        "case_feat_names": list(
            config.get("case_feat_names") or DEFAULT_FEATURE_ORDER
        ),
        "label_config": _normalise_label_config(config),
        "model_path": _relative_to_backend(model_path),
        "scaler_path": _relative_to_backend(scaler_path) if scaler_path else None,
    }


def _find_model_path(model_dir: Path) -> Path | None:
    candidates = [
        path
        for path in model_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in MODEL_FILE_SUFFIXES
    ]
    if not candidates:
        return None

    preferred_prefixes = ("best_model", "model", "checkpoint")
    return sorted(
        candidates,
        key=lambda path: (
            not path.stem.startswith(preferred_prefixes),
            path.name,
        ),
    )[0]


def _configured_path(
    config: dict[str, Any],
    model_dir: Path,
    keys: tuple[str, ...],
) -> Path | None:
    for key in keys:
        value = config.get(key)
        if not value:
            continue

        path = Path(value)
        if not path.is_absolute():
            path = model_dir / path
        if path.exists():
            return path

    return None


def _find_scaler_path(model_dir: Path) -> Path | None:
    candidates = [
        path
        for path in model_dir.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower() in SCALER_FILE_SUFFIXES
            and "scaler" in path.stem.lower()
        )
    ]
    return sorted(candidates, key=lambda path: path.name)[0] if candidates else None


def _normalise_label_config(config: dict[str, Any]) -> dict[str, Any]:
    label_config = config.get("label_config")
    if isinstance(label_config, dict):
        return label_config

    inferred_label_config = {}
    for key in (
        "classif_thresh",
        "top_bottom_percent",
        "top_quantile_threshold",
        "bottom_quantile_threshold",
    ):
        if key in config:
            inferred_label_config[key] = config[key]

    return inferred_label_config


def _relative_to_backend(path: Path) -> str:
    try:
        return path.resolve().relative_to(BACKEND_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def _upsert_model_config(db: Session, values: dict[str, Any]) -> ModelConfig:
    existing_config = db.scalar(
        select(ModelConfig).where(ModelConfig.name == values["name"])
    )

    if existing_config is None:
        model_config = ModelConfig(**values)
        db.add(model_config)
        return model_config

    for key, value in values.items():
        setattr(existing_config, key, value)
    return existing_config


def _seed_feature_importances(
    db: Session,
    model_config: ModelConfig,
    model_dir: Path,
) -> None:
    importance_path = model_dir / FEATURE_VALIDATION_SUMMARY
    case_attention_path = model_dir / CASE_FEATURE_ATTENTION_TEST
    importances = _read_mean_permutation_importances(importance_path)

    if not importances:
        feature_names = _feature_names_from_case_attention(case_attention_path) or list(DEFAULT_FEATURE_ORDER)
        importances = {feature_name: 0.0 for feature_name in feature_names}

    existing_rows = {
        row.feature_name: row
        for row in db.scalars(
            select(ModelFeatureImportance).where(
                ModelFeatureImportance.config_id == model_config.config_id
            )
        )
    }

    for feature_name, mean_importance in importances.items():
        existing_row = existing_rows.get(feature_name)
        if existing_row is None:
            db.add(
                ModelFeatureImportance(
                    config_id=model_config.config_id,
                    feature_name=feature_name,
                    mean_permutation_importance=mean_importance,
                )
            )
            continue

        existing_row.mean_permutation_importance = mean_importance


def _read_mean_permutation_importances(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}

    importances: dict[str, float] = {}
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            feature_name = (row.get("Feature") or "").strip()
            if not feature_name:
                continue
            importances[feature_name] = _safe_float(
                row.get("MeanPermutationImportance"),
                default=0.0,
            )
    return importances


def _feature_names_from_case_attention(path: Path) -> list[str]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []

    feature_names: list[str] = []
    seen = set()
    for fieldname in fieldnames:
        feature_name = _strip_attribution_suffix(fieldname)
        if feature_name is None or feature_name in seen:
            continue
        seen.add(feature_name)
        feature_names.append(feature_name)
    return feature_names


def _strip_attribution_suffix(fieldname: str) -> str | None:
    for suffix in ATTRIBUTION_SUFFIXES:
        if fieldname.endswith(suffix):
            return fieldname[: -len(suffix)]
    return None


def _seed_case_feature_contributions(
    db: Session,
    model_config: ModelConfig,
    model_dir: Path,
) -> None:
    case_attention_path = model_dir / CASE_FEATURE_ATTENTION_TEST
    if not case_attention_path.exists():
        return

    with case_attention_path.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            case_id = _normalise_case_id(row.get("Case ID"))
            if not case_id:
                continue

            document = db.scalar(
                select(DocumentMetadata).where(DocumentMetadata.case_id == case_id)
            )
            if document is None:
                continue

            inference = db.scalar(
                select(Inference).where(
                    Inference.config_id == model_config.config_id,
                    Inference.document_id == document.document_id,
                )
            )
            if inference is None:
                inference = Inference(
                    config_id=model_config.config_id,
                    document_id=document.document_id,
                )
                db.add(inference)

            score = _safe_float(row.get("Prediction"), default=None)
            true_label = _safe_float(row.get("Label"), default=None)
            inference.score = score
            inference.true_label = true_label
            inference.prediction_label = _prediction_label(score)
            inference.narrative_contribution = _safe_float(
                row.get("LLM_Branch_Contribution"),
                default=0.0,
            )
            inference.feature_contribution = _safe_float(
                row.get("Handcrafted_Branch_Contribution"),
                default=0.0,
            )


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


def _normalise_case_id(value: Any) -> str:
    if value in (None, ""):
        return ""
    numeric_case_id = _safe_int(value)
    if numeric_case_id is not None:
        return str(numeric_case_id)
    return str(value).strip()


def _prediction_label(score: float | None) -> str | None:
    if score is None:
        return None
    return "High" if score >= 0.5 else "Low"
