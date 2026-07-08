from pathlib import Path
from typing import Any

from app.crud import GTF_ORDER
from app.database import SessionLocal
from app.models.inference import ModelConfig
from app.pipeline.embedder import embedder
from app.pipeline.feature_extractor import (
    ENTITY_LISTS_KEY,
    SPACY_ENTITY_LABELS,
    feature_extractor,
)
from app.services.inference_service import inference_engine


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class PipelineManager:
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
        if model_config["input_dim"] is None:
            model_config["input_dim"] = len(embeddings[0])

        prediction = inference_engine.run_inference(
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
            "features": features,
            "entities": entities,
            "ordered_features": ordered_features,
            "feature_names": model_config["feature_names"],
            "feature_gates": prediction.get("feature_gates", []),
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

    def _get_config(self, config_id: int | str | None) -> ModelConfig:
        if config_id is None:
            raise ValueError("A model config or config_id is required for inference.")

        with SessionLocal() as db:
            config = db.get(ModelConfig, int(config_id))
            if config is None:
                raise ValueError(f"Model configuration {config_id} was not found.")
            return config

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
            or GTF_ORDER
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
