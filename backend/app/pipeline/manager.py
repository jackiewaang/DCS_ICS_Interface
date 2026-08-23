from typing import Any

from app.clients.embedding_client import EmbeddingClient
from app.models.inference import ModelConfig
from app.pipeline.embedding_preprocessor import EmbeddingPreprocessor
from app.pipeline.embedding_saver import EmbeddingSaver
from app.pipeline.feature_vector_builder import FeatureVectorBuilder
from app.pipeline.model_config_resolver import ModelConfigResolver
from app.pipeline.model_runner import ModelRunner
from app.repositories.model_config_repository import get_model_config


SAVE_EMBEDDINGS_PICKLE = False
EMBEDDING_SERVER_URL = "http://localhost:8001"
CLASSIFICATION_PROMPT = (
    "Given a text from a research impact report, classify the research impact "
    "into high-quality or low-quality: "
)


class PipelineManager:
    def __init__(
        self,
        model_runner: ModelRunner | None = None,
        embedding_preprocessor: EmbeddingPreprocessor | None = None,
        embedding_client: EmbeddingClient | None = None,
        model_config_resolver: ModelConfigResolver | None = None,
        feature_vector_builder: FeatureVectorBuilder | None = None,
        embedding_saver: EmbeddingSaver | None = None,
    ):
        self.model_runner = model_runner or ModelRunner()
        self.embedding_preprocessor = embedding_preprocessor or EmbeddingPreprocessor()
        self.embedding_client = embedding_client or EmbeddingClient(EMBEDDING_SERVER_URL)
        self.model_config_resolver = model_config_resolver or ModelConfigResolver()
        self.feature_vector_builder = feature_vector_builder or FeatureVectorBuilder()
        self.embedding_saver = embedding_saver or EmbeddingSaver()

    def run_inference(
        self,
        sections: dict[str, str],
        config_id: int | str | None = None,
        config: dict[str, Any] | ModelConfig | None = None,
    ) -> dict[str, Any]:
        model_config = self.model_config_resolver.normalise(
            config or get_model_config(config_id)
        )
        summary_text = sections.get("summary") or ""
        research_text = sections.get("research") or ""
        impact_text = sections.get("impact") or ""

        features, entities, ordered_features = self.feature_vector_builder.build(
            summary_text=summary_text,
            details_text=impact_text,
            config=model_config,
        )

        sentences = self.embedding_preprocessor.prepare_sentences(
            summary=summary_text,
            research=research_text,
            details=impact_text,
        )
        if not sentences:
            raise ValueError("No text was available to embed for inference.")

        embeddings = self.embedding_client.embed(
            texts=sentences,
            prompt=CLASSIFICATION_PROMPT,
        )
        if not embeddings:
            raise ValueError("The embedding server returned no embeddings.")
        if len(embeddings) != len(sentences):
            raise ValueError("The embedding count does not match the sentence count.")

        embeddings_path = None
        if SAVE_EMBEDDINGS_PICKLE:
            embeddings_path = self.embedding_saver.save(
                sentences,
                embeddings,
                model_config,
                sections,
            )
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
                "attention": float(attention[index]),
            }
            for index, sentence in enumerate(sentences)
            if index < len(attention)
        ]

        return {
            "score": prediction["score"],
            "label": prediction["label"],
            "attention": attention,
            "heatmap": heatmap,
            "sentences": sentences,
            "embeddings_path": str(embeddings_path) if embeddings_path else None,
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
