import unittest

from app.clients.hybrid_embedding_client import HybridEmbeddingClient
from slurmBackend.backend import SlurmCompletionTimeout


class FakeAquiferClient:
    def __init__(self, result=None):
        self.result = result or [[9.0, 8.0]]
        self.calls = []

    def embed(self, texts, prompt=None):
        self.calls.append({"texts": texts, "prompt": prompt})
        return self.result


class FakeSlurmBackend:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.requests = []

    def run_embedding(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.result


class HybridEmbeddingClientTests(unittest.TestCase):
    def test_uses_slurm_result_without_calling_aquifer(self):
        aquifer = FakeAquiferClient()
        slurm = FakeSlurmBackend(result={"embeddings": [[1.0, 2.0]]})
        client = HybridEmbeddingClient(aquifer, slurm, model_name="test/model")

        result = client.embed(
            ["text"],
            prompt="prompt",
            model_name="selected/model",
        )

        self.assertEqual(result, [[1.0, 2.0]])
        self.assertEqual(aquifer.calls, [])
        self.assertEqual(slurm.requests[0].model_name, "selected/model")

    def test_falls_back_to_aquifer_on_slurm_timeout(self):
        aquifer = FakeAquiferClient()
        slurm = FakeSlurmBackend(error=SlurmCompletionTimeout("timed out"))
        client = HybridEmbeddingClient(aquifer, slurm, model_name="test/model")

        result = client.embed(["text"], prompt="prompt")

        self.assertEqual(result, [[9.0, 8.0]])
        self.assertEqual(len(aquifer.calls), 1)

    def test_falls_back_to_aquifer_on_malformed_slurm_result(self):
        aquifer = FakeAquiferClient()
        slurm = FakeSlurmBackend(result={"embeddings": []})
        client = HybridEmbeddingClient(aquifer, slurm, model_name="test/model")

        result = client.embed(["text"])

        self.assertEqual(result, [[9.0, 8.0]])
        self.assertEqual(len(aquifer.calls), 1)


if __name__ == "__main__":
    unittest.main()
