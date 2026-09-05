import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.model_configs import ModelConfig
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
            _seed_feature_importances(db_model_config, config_path.parent)
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
        "description": config.get("description") or None,
        "emb_model": config.get("emb_model"),
        "run_mode": config.get("run_mode"),
        "fusion_type": config.get("fusion_type") or "gated",
        "case_feat_names": list(
            config.get("case_feat_names") or DEFAULT_FEATURE_ORDER
        ),
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
    model_config: ModelConfig,
    model_dir: Path,
) -> None:
    importance_path = model_dir / FEATURE_VALIDATION_SUMMARY
    case_attention_path = model_dir / CASE_FEATURE_ATTENTION_TEST
    importances = _read_mean_permutation_importances(importance_path)

    if not importances:
        feature_names = _feature_names_from_case_attention(case_attention_path) or list(DEFAULT_FEATURE_ORDER)
        importances = {feature_name: 0.0 for feature_name in feature_names}

    model_config.feature_importances = importances


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


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

