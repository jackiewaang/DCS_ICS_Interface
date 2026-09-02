import logging
from numbers import Real

from app.clients.embedding_client import EmbeddingClient
from slurmBackend.backend import EmbeddingJobRequest, SlurmBackend
from slurmBackend.config import SlurmConfig


logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-4B"


class HybridEmbeddingClient:
    """Use Slurm for embeddings and fall back to the Aquifer HTTP service."""

    def __init__(
        self,
        aquifer_client: EmbeddingClient,
        slurm_backend: SlurmBackend | None = None,
        model_name: str | None = None,
    ) -> None:
        self.aquifer_client = aquifer_client
        self.slurm_backend = slurm_backend or SlurmBackend(SlurmConfig.from_env())
        self.model_name = model_name or DEFAULT_EMBEDDING_MODEL

    def embed(
        self,
        texts: list[str],
        prompt: str | None = None,
        model_name: str | None = None,
    ) -> list[list[float]]:
        try:
            result = self.slurm_backend.run_embedding(
                EmbeddingJobRequest(
                    texts=texts,
                    model_name=model_name or self.model_name,
                    prompt=prompt,
                )
            )
            return self._validate_embeddings(result, expected_count=len(texts))
        except Exception:
            logger.warning(
                "Slurm embedding failed; falling back to Aquifer",
                exc_info=True,
            )
            return self.aquifer_client.embed(texts=texts, prompt=prompt)

    @staticmethod
    def _validate_embeddings(
        result: object,
        expected_count: int,
    ) -> list[list[float]]:
        if not isinstance(result, dict):
            raise ValueError("Slurm embedding result must be a JSON object.")

        embeddings = result.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise ValueError("Slurm returned no embeddings.")
        if len(embeddings) != expected_count:
            raise ValueError("Slurm embedding count does not match the text count.")
        if any(
            not isinstance(vector, list)
            or not vector
            or any(not isinstance(value, Real) for value in vector)
            for vector in embeddings
        ):
            raise ValueError("Slurm returned malformed embeddings.")

        return embeddings
