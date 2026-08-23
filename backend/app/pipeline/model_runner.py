# Loads and caches trained AttentionMIL assets, then runs local model inference.

from typing import Any

import joblib
import torch

from app.pipeline.attention_mil import AttentionMIL


class ModelRunner:
    def __init__(self, device: str | None = None):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        # cache models and scalers after first use
        self.loaded_models: dict[Any, AttentionMIL] = {}
        self.loaded_scalers: dict[Any, Any] = {}

    def run_inference(
        self,
        config: dict[str, Any],
        embeddings: list[list[float]],
        ordered_features: list[float] | None = None
    ) -> dict[str, Any]:
        model, scaler = self._get_assets(config)

        feature_tensor = None

        if ordered_features:
            features = (
                scaler.transform([ordered_features])[0]
                if scaler
                else ordered_features
            )

            feature_tensor = torch.tensor(features, dtype=torch.float32).to(self.device)
        
        embedding_tensor = torch.tensor(embeddings, dtype=torch.float32).to(self.device)

        with torch.no_grad():
            (
                prediction,
                attention,
                gates,
                text_importance,
                feature_importance
            ) = model(embedding_tensor, case_features=feature_tensor)

        score = round(float(prediction.item()), 4)

        return {
            "score": score,
            "label": "High Impact" if score >= 0.5 else "Low Impact",
            "attention": attention.detach().view(-1).cpu().numpy().tolist(),
            "feature_gates": (
                gates.detach().view(-1).cpu().numpy().tolist()
                if gates is not None
                else []
            ),
            "narrative_contribution": round(float(text_importance.item()), 4),
            "feature_contribution": round(float(feature_importance.item()), 4),
        }

    def _get_assets(self, config: dict[str, Any]) -> tuple[AttentionMIL, Any]:
        config_id = config["config_id"]
        if config_id in self.loaded_models:
            return self.loaded_models[config_id], self.loaded_scalers.get(config_id)

        scaler = joblib.load(config["scaler_path"]) if config.get("scaler_path") else None
        feature_dim = config["feature_dim"] if config.get("use_features") else None

        model = AttentionMIL(
            input_dim=config["input_dim"],
            hidden_dim=config.get("hidden_dim", 128),
            case_feat_dim=feature_dim,
            fusion_type=config.get("fusion_type", "gated"),
            mode=config.get("task", "classification"),
        )

        checkpoint = torch.load(config["checkpoint_path"], map_location=self.device)
        state_dict = checkpoint.get("model_state_dict", checkpoint)
        model.load_state_dict(state_dict)
        model.to(self.device).eval()

        self.loaded_models[config_id] = model
        self.loaded_scalers[config_id] = scaler
        return model, scaler
