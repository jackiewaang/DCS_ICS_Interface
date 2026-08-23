# Extracts document features, enriches entity counts, and orders values for a model.

from typing import Any

from app.pipeline.feature_extractor import (
    ENTITY_LISTS_KEY,
    SPACY_ENTITY_LABELS,
    FeatureExtractorEngine,
    feature_extractor,
)


class FeatureVectorBuilder:
    def __init__(self, extractor: FeatureExtractorEngine | None = None):
        self.extractor = extractor or feature_extractor

    def build(
        self,
        summary_text: str,
        details_text: str,
        config: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, list[str]], list[float]]:
        features = self.extractor.extract(
            summary_text=summary_text,
            details_text=details_text,
        )
        entities = features.pop(ENTITY_LISTS_KEY, {})
        self._add_entity_count_features(features, entities)
        ordered_values = self._ordered_values(features, entities, config)
        return features, entities, ordered_values

    def _ordered_values(
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
        if feature_name in SPACY_ENTITY_LABELS:
            return len(entities.get(feature_name, []))
        return features.get(feature_name, 0)
