# Provides database access for model configurations and global feature importance.

from sqlalchemy import select

from app.database import SessionLocal
from app.models.inference import ModelConfig, ModelFeatureImportance


def get_model_config(config_id: int | str | None) -> ModelConfig:
    if config_id is None:
        raise ValueError("A model config or config_id is required for inference.")

    with SessionLocal() as db:
        config = db.get(ModelConfig, int(config_id))
        if config is None:
            raise ValueError(f"Model configuration {config_id} was not found.")
        return config


def get_global_importance(
    config_id: int | str | None,
    feature_names: list[str] | None = None,
) -> dict[str, float]:
    try:
        numeric_config_id = int(config_id)
    except (TypeError, ValueError):
        return {}

    with SessionLocal() as db:
        rows = db.scalars(
            select(ModelFeatureImportance).where(
                ModelFeatureImportance.config_id == numeric_config_id
            )
        ).all()

    if rows:
        return {
            row.feature_name: row.mean_permutation_importance
            for row in rows
        }
    return {feature_name: 0.0 for feature_name in feature_names or []}
