# Sends prepared text to the embedding server and returns its generated vectors.

import requests

class EmbeddingClient:
    def __init__(self, base_url: str, timeout: float = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def embed(
        self,
        texts: list[str],
        prompt: str | None = None
    ) -> list[list[float]]:
        response = requests.post(
            f"{self.base_url}/embed",
            json={
                "texts": texts,
                "prompt": prompt,
            },
            timeout=self.timeout
        )

        response.raise_for_status()

        return response.json().get("embeddings", [])
