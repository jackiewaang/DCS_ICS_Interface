import os

import requests


class AquiferEmbeddingClient:
    def __init__(self, base_url: str | None = None, timeout: float = 300):
        self.base_url = (
            base_url
            or os.getenv("AQUIFER_EMBEDDING_URL")
            or "http://127.0.0.1:8001"
        ).rstrip("/")
        self.timeout = timeout

    def embed(
        self,
        texts: list[str],
        prompt: str | None = None,
    ) -> list[list[float]]:
        response = requests.post(
            f"{self.base_url}/embed",
            json={"texts": texts, "prompt": prompt},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json().get("embeddings", [])
