# Provides database access for model configurations and global feature importance.

from app.database import SessionLocal
from app.models.model_configs import ModelConfig


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
        config = db.get(ModelConfig, numeric_config_id)
        if config and config.feature_importances:
            return dict(config.feature_importances)

    return {feature_name: 0.0 for feature_name in feature_names or []}
