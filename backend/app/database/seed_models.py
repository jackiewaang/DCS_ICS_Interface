import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.inference import ModelConfig


BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODELS_ROOT = BACKEND_ROOT / "assets" / "models"

MODEL_FILE_SUFFIXES = (".pth", ".pt", ".bin", ".safetensors")
SCALER_FILE_SUFFIXES = (".joblib", ".pkl", ".pickle")


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

            _upsert_model_config(db, model_config)
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


def _upsert_model_config(db: Session, values: dict[str, Any]) -> None:
    existing_config = db.scalar(
        select(ModelConfig).where(ModelConfig.name == values["name"])
    )

    if existing_config is None:
        db.add(ModelConfig(**values))
        return

    for key, value in values.items():
        setattr(existing_config, key, value)
