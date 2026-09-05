import logging
from numbers import Real


logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, slurm_client, aquifer_client):
        self.slurm_client = slurm_client
        self.aquifer_client = aquifer_client

    def embed(
        self,
        texts: list[str],
        prompt: str | None = None,
        model_name: str | None = None,
    ) -> list[list[float]]:
        try:
            result = self.slurm_client.embed(
                texts=texts,
                prompt=prompt,
                model_name=model_name,
            )
            return self._validate(result, len(texts))
        except Exception:
            logger.warning(
                "Slurm embedding failed; falling back to Aquifer",
                exc_info=True,
            )

        result = self.aquifer_client.embed(texts=texts, prompt=prompt)
        return self._validate(result, len(texts))

    @staticmethod
    def _validate(result: object, expected_count: int) -> list[list[float]]:
        embeddings = result.get("embeddings") if isinstance(result, dict) else result

        if not isinstance(embeddings, list) or not embeddings:
            raise ValueError("Embedding response is empty or malformed.")
        if len(embeddings) != expected_count:
            raise ValueError("Embedding count does not match the input count.")
        if any(
            not isinstance(vector, list)
            or not vector
            or any(not isinstance(value, Real) for value in vector)
            for vector in embeddings
        ):
            raise ValueError("Embedding response contains malformed vectors.")

        return embeddings
