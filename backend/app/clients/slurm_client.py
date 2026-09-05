from slurmBackend.backend import EmbeddingJobRequest, SlurmBackend
from slurmBackend.config import SlurmConfig


DEFAULT_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-4B"
DEFAULT_LLM_MODEL = "Qwen/Qwen3-4B-Instruct-2507"


class SlurmClient:
    def __init__(self, backend: SlurmBackend | None = None):
        self.backend = backend or SlurmBackend(SlurmConfig.from_env())

    def embed(
        self,
        texts: list[str],
        prompt: str | None = None,
        model_name: str | None = None,
    ) -> dict:
        return self.backend.run_embedding(
            EmbeddingJobRequest(
                texts=texts,
                model_name=model_name or DEFAULT_EMBEDDING_MODEL,
                prompt=prompt,
            )
        )

    def generate(
        self,
        messages: list[dict],
        model_name: str | None = None,
    ) -> dict:
        return self.backend.run_llm(
            {"messages": messages},
            model_name or DEFAULT_LLM_MODEL,
        )
