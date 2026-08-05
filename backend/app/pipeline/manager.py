from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import joblib
import pandas as pd
import torch
from sqlalchemy import select

from app.database import SessionLocal
from app.models.inference import ModelConfig, ModelFeatureImportance
from app.pipeline.embedder import embedder
from app.pipeline.feature_extractor import (
    ENTITY_LISTS_KEY,
    SPACY_ENTITY_LABELS,
    feature_extractor,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
EMBEDDINGS_OUTPUT_DIR = BACKEND_ROOT / "embeddings"
DEFAULT_FEATURE_ORDER = [
    "Flesch Reading Ease",
    "Dale-Chall Readability Score",
    "SMOG Index",
    "Automated Readability Index",
    "Sentiment (mean)",
    "Sentiment (10th)",
    "Sentiment (50th)",
    "Sentiment (75th)",
    "Sentiment (90th)",
    "Number of organizations mentioned",
    "Number of named individuals",
    "Number of countries or regions mentioned",
    "Word count",
    "Paragraph count",
    "PERSON",
    "NORP",
    "FAC",
    "ORG",
    "GPE",
    "LOC",
    "PRODUCT",
    "EVENT",
    "WORK_OF_ART",
    "LAW",
    "LANGUAGE",
    "DATE",
    "TIME",
    "PERCENT",
    "MONEY",
    "QUANTITY",
    "ORDINAL",
    "CARDINAL",
]


class AttentionMIL(torch.nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        output_dim: int = 1,
        mode: str = "classification",
        case_feat_dim: int | None = None,
        fusion_type: str = "gated",
    ):
        super().__init__()
        self.mode = mode
        self.case_feat_dim = case_feat_dim
        self.fusion_type = fusion_type

        self.attention = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.Tanh(),
            torch.nn.Linear(hidden_dim, 1),
        )
        self.sentence_proj = torch.nn.Linear(input_dim, hidden_dim)

        if case_feat_dim is not None:
            self.feature_gate = torch.nn.Sequential(
                torch.nn.Linear(case_feat_dim, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, case_feat_dim),
            )
            self.case_mlp = torch.nn.Sequential(
                torch.nn.Linear(case_feat_dim, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Dropout(0.2),
                torch.nn.Linear(hidden_dim, hidden_dim),
            )

        if case_feat_dim is None:
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, output_dim),
            )
        elif fusion_type == "gated":
            self.gate = torch.nn.Sequential(
                torch.nn.Linear(hidden_dim * 2, hidden_dim),
                torch.nn.Sigmoid(),
            )
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, output_dim),
            )
        else:
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim * 2, output_dim),
            )

    def encode_text(self, embeddings: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        attention_scores = torch.softmax(self.attention(embeddings), dim=0)
        text_repr = torch.sum(attention_scores * embeddings, dim=0, keepdim=True)
        return self.sentence_proj(text_repr), attention_scores

    def encode_features(self, case_features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        gate_logits = self.feature_gate(case_features)
        feature_gates = torch.sigmoid(gate_logits)
        gated_features = feature_gates * case_features
        return self.case_mlp(gated_features), feature_gates

    def fuse(
        self,
        text_repr: torch.Tensor,
        feature_repr: torch.Tensor | None,
    ) -> torch.Tensor:
        if feature_repr is None:
            return text_repr

        if text_repr.dim() == 1:
            text_repr = text_repr.unsqueeze(0)
        if feature_repr.dim() == 1:
            feature_repr = feature_repr.unsqueeze(0)

        if self.fusion_type == "gated":
            fusion = torch.cat([text_repr, feature_repr], dim=-1)
            gate = self.gate(fusion)
            fused = gate * text_repr + (1 - gate) * feature_repr
        else:
            fused = torch.cat([text_repr, feature_repr], dim=-1)

        return fused.squeeze(0)

    def predict_from_repr(self, fused_repr: torch.Tensor) -> torch.Tensor:
        output = self.classifier(fused_repr)
        if self.mode == "classification":
            return torch.sigmoid(output)
        return output

    def forward(
        self,
        embeddings: torch.Tensor,
        case_features: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None, torch.Tensor, torch.Tensor]:
        eps = 1e-8
        text_repr, attention_scores = self.encode_text(embeddings)

        if case_features is not None:
            feature_repr, feature_gates = self.encode_features(case_features)
        else:
            feature_repr = None
            feature_gates = None

        fused = self.fuse(text_repr, feature_repr)
        prediction = self.predict_from_repr(fused)

        if feature_repr is not None:
            zero_feature = torch.zeros_like(feature_repr)
            text_only = self.predict_from_repr(self.fuse(text_repr, zero_feature))

            zero_text = torch.zeros_like(text_repr)
            feature_only = self.predict_from_repr(self.fuse(zero_text, feature_repr))

            text_delta = torch.abs(prediction - feature_only)
            feature_delta = torch.abs(prediction - text_only)
            total_delta = torch.abs(text_delta) + torch.abs(feature_delta) + eps

            text_importance = (text_delta / total_delta).clamp(0, 1)
            feature_importance = (feature_delta / total_delta).clamp(0, 1)
        else:
            text_importance = torch.tensor(1.0, device=embeddings.device)
            feature_importance = torch.tensor(0.0, device=embeddings.device)

        return (
            prediction,
            attention_scores,
            feature_gates,
            text_importance,
            feature_importance,
        )


class ModelRunner:
    def __init__(self):
        self.loaded_models: dict[Any, AttentionMIL] = {}
        self.loaded_scalers: dict[Any, Any] = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def run_inference(
        self,
        config: dict[str, Any],
        embeddings: list[list[float]],
        ordered_features: list[float] | None = None,
    ) -> dict[str, Any]:
        model, scaler = self._get_assets(config)

        feature_tensor = None
        if ordered_features:
            features = scaler.transform([ordered_features])[0] if scaler else ordered_features
            feature_tensor = torch.tensor(features, dtype=torch.float32).to(self.device)

        embedding_tensor = torch.tensor(embeddings, dtype=torch.float32).to(self.device)

        with torch.no_grad():
            prediction, attention, gates, text_importance, feature_importance = model(
                embedding_tensor,
                case_features=feature_tensor,
            )

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


class PipelineManager:
    def __init__(self, model_runner: ModelRunner | None = None):
        self.model_runner = model_runner or ModelRunner()

    def run_inference(
        self,
        sections: dict[str, str] | str,
        config_id: int | str | None = None,
        config: dict[str, Any] | ModelConfig | None = None,
    ) -> dict[str, Any]:
        model_config = self._normalise_config(config or self._get_config(config_id))
        summary_text, research_text, impact_text = self._normalise_sections(sections)

        features = feature_extractor.extract(
            summary_text=summary_text,
            details_text=impact_text,
        )
        entities = features.pop(ENTITY_LISTS_KEY, {})
        self._add_entity_count_features(features, entities)
        ordered_features = self._ordered_feature_values(features, entities, model_config)

        sentences, embeddings = embedder.run_embedding_inference(
            summary_text=summary_text,
            research_text=research_text,
            details_text=impact_text,
            model_name=model_config["embedding_name"],
            granularity=model_config["input_granularity"],
        )
        if not embeddings:
            raise ValueError("No text was available to embed for inference.")
        embeddings_path = self._save_embeddings(sentences, embeddings, model_config)
        if model_config["input_dim"] is None:
            model_config["input_dim"] = len(embeddings[0])

        prediction = self.model_runner.run_inference(
            model_config,
            embeddings,
            ordered_features if model_config["use_features"] else None,
        )

        attention = prediction.get("attention") or []
        heatmap = [
            {
                "sentence": sentence,
                "attention": float(attention[idx]),
            }
            for idx, sentence in enumerate(sentences)
            if idx < len(attention)
        ]

        return {
            "score": prediction["score"],
            "label": prediction["label"],
            "attention": attention,
            "heatmap": heatmap,
            "sentences": sentences,
            "embeddings_path": str(embeddings_path),
            "features": features,
            "entities": entities,
            "ordered_features": ordered_features,
            "feature_names": model_config["feature_names"],
            "feature_gates": prediction.get("feature_gates", []),
            "global_importance": self._get_global_importance(model_config["config_id"]),
            "narrative_contribution": prediction.get("narrative_contribution"),
            "feature_contribution": prediction.get("feature_contribution"),
            "model": {
                "config_id": model_config.get("config_id"),
                "name": model_config.get("name"),
                "embedding_name": model_config["embedding_name"],
                "input_granularity": model_config["input_granularity"],
                "task": model_config["task"],
            },
        }

    def _save_embeddings(
        self,
        sentences: list[str],
        embeddings: list[list[float]],
        model_config: dict[str, Any],
    ) -> Path:
        EMBEDDINGS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output_path = EMBEDDINGS_OUTPUT_DIR / f"embeddings_{timestamp}_{uuid4().hex}.pkl"
        output_df = pd.DataFrame(
            {
                "input": sentences,
                "embeddings": embeddings,
            }
        )
        output_df["config_id"] = model_config.get("config_id")
        output_df["embedding_name"] = model_config.get("embedding_name")
        output_df["input_granularity"] = model_config.get("input_granularity")
        output_df.to_pickle(output_path)

        return output_path

    def _get_config(self, config_id: int | str | None) -> ModelConfig:
        if config_id is None:
            raise ValueError("A model config or config_id is required for inference.")

        with SessionLocal() as db:
            config = db.get(ModelConfig, int(config_id))
            if config is None:
                raise ValueError(f"Model configuration {config_id} was not found.")
            return config

    def _get_global_importance(self, config_id: int | str) -> dict[str, float]:
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

            return {
                row.feature_name: row.mean_permutation_importance
                for row in rows
            }

    def _normalise_sections(self, sections: dict[str, str] | str) -> tuple[str, str, str]:
        if isinstance(sections, str):
            return "", "", sections

        return (
            sections.get("summary") or sections.get("summary_text") or "",
            sections.get("research") or sections.get("research_text") or "",
            sections.get("impact")
            or sections.get("details")
            or sections.get("details_text")
            or "",
        )

    def _normalise_config(self, config: dict[str, Any] | ModelConfig) -> dict[str, Any]:
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

        normalised = {
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

        return normalised

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
        return str((BACKEND_ROOT / path).resolve())

    def _ordered_feature_values(
        self,
        features: dict[str, Any],
        entities: dict[str, list[str]],
        config: dict[str, Any],
    ) -> list[float]:
        values = []
        for feature_name in config["feature_names"][: config["feature_dim"]]:
            value = self._feature_value(feature_name, features, entities)
            if isinstance(value, str):
                value = 0
            values.append(float(value or 0))
        return values

    def _add_entity_count_features(
        self,
        features: dict[str, Any],
        entities: dict[str, list[str]],
    ) -> None:
        features["Number of organizations mentioned"] = len(entities.get("ORG", []))
        features["Number of named individuals"] = len(entities.get("PERSON", []))
        features["Number of countries or regions mentioned"] = (
            len(entities.get("GPE", [])) + len(entities.get("LOC", []))
        )

    def _feature_value(
        self,
        feature_name: str,
        features: dict[str, Any],
        entities: dict[str, list[str]],
    ) -> Any:
        if feature_name == "Number of organizations mentioned":
            return len(entities.get("ORG", []))
        if feature_name == "Number of named individuals":
            return len(entities.get("PERSON", []))
        if feature_name == "Number of countries or regions mentioned":
            return len(entities.get("GPE", [])) + len(entities.get("LOC", []))
        if feature_name in SPACY_ENTITY_LABELS:
            return len(entities.get(feature_name, []))
        return features.get(feature_name, 0)


pipeline_manager = PipelineManager()
