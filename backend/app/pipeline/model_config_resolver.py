# Normalizes database or ad-hoc model settings into the configuration used for inference.

from pathlib import Path
from typing import Any

from app.models.model_configs import ModelConfig
from app.pipeline.feature_schema import DEFAULT_FEATURE_ORDER


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class ModelConfigResolver:
    def __init__(self, backend_root: Path = BACKEND_ROOT):
        self.backend_root = backend_root

    def normalise(self, config: dict[str, Any] | ModelConfig) -> dict[str, Any]:
        if isinstance(config, ModelConfig):
            raw = {
                column.name: getattr(config, column.name)
                for column in config.__table__.columns
            }
        else:
            raw = dict(config)

        model_path = raw.get("checkpoint_path") or raw.get("model_path")
        if not model_path:
            raise ValueError("Model configuration must include model_path or checkpoint_path.")

        scaler_path = raw.get("scaler_path")
        feature_names = (
            raw.get("case_feat_names")
            or raw.get("feature_names")
            or DEFAULT_FEATURE_ORDER
        )

        return {
            **raw,
            "config_id": raw.get("config_id") or raw.get("id") or f"adhoc:{model_path}",
            "checkpoint_path": self._resolve_asset_path(model_path),
            "scaler_path": self._resolve_asset_path(scaler_path) if scaler_path else None,
            "embedding_name": (
                raw.get("embedding_name")
                or raw.get("emb_model")
                or raw.get("model_name")
                or "all-roberta-large-v1"
            ),
            "input_granularity": (
                raw.get("input_granularity")
                or raw.get("emb_mode")
                or raw.get("granularity")
                or "sentence"
            ),
            "task": raw.get("task") or raw.get("run_mode") or "classification",
            "fusion_type": raw.get("fusion_type") or "gated",
            "input_dim": (
                int(raw.get("input_dim") or raw.get("embedding_dim"))
                if raw.get("input_dim") or raw.get("embedding_dim")
                else None
            ),
            "feature_dim": int(raw.get("feature_dim") or len(feature_names)),
            "hidden_dim": int(raw.get("hidden_dim") or 128),
            "use_features": self._uses_features(raw, feature_names),
            "feature_names": list(feature_names),
        }

    def _uses_features(self, config: dict[str, Any], feature_names: list[str]) -> bool:
        if "use_features" in config:
            return bool(config["use_features"])
        if "feature_dim" in config:
            return bool(config["feature_dim"])
        return bool(feature_names)

    def _resolve_asset_path(self, path: str | Path) -> str:
        path = Path(path)
        if path.is_absolute():
            return str(path)
        return str((self.backend_root / path).resolve())
