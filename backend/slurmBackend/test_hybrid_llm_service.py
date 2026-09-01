import unittest
from unittest.mock import AsyncMock, patch

from app.llm import service
from slurmBackend.backend import SlurmCompletionTimeout


VALID_FEEDBACK = {
    "significance_limitations": [],
    "significance_improvements": [],
    "outreach_limitations": [],
    "outreach_improvements": [],
}

LLM_INPUT = {
    "prediction_label": "high-quality",
    "score": 0.85,
    "top_sentences": [],
    "top_features": [],
    "summary": "Summary",
    "details": "Details",
    "model_name": "selected/model",
}


class FakeSlurmBackend:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def run_llm(self, payload, model_name):
        self.calls.append({"payload": payload, "model_name": model_name})
        if self.error:
            raise self.error
        return self.result


class HybridLlmServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_slurm_result_without_calling_aquifer(self):
        slurm = FakeSlurmBackend(result=VALID_FEEDBACK)
        aquifer = AsyncMock()

        with (
            patch.object(service, "slurm_backend", slurm),
            patch.object(service, "generate", aquifer),
        ):
            result = await service.generate_feedback(LLM_INPUT)

        self.assertEqual(result, VALID_FEEDBACK)
        aquifer.assert_not_awaited()
        self.assertEqual(slurm.calls[0]["model_name"], "selected/model")

    async def test_falls_back_to_aquifer_on_slurm_timeout(self):
        slurm = FakeSlurmBackend(error=SlurmCompletionTimeout("timed out"))
        aquifer = AsyncMock(return_value=_valid_feedback_json())

        with (
            patch.object(service, "slurm_backend", slurm),
            patch.object(service, "generate", aquifer),
        ):
            result = await service.generate_feedback(LLM_INPUT)

        self.assertEqual(result, VALID_FEEDBACK)
        aquifer.assert_awaited_once()

    async def test_falls_back_to_aquifer_on_malformed_slurm_result(self):
        slurm = FakeSlurmBackend(result={"unexpected": "value"})
        aquifer = AsyncMock(return_value=_valid_feedback_json())

        with (
            patch.object(service, "slurm_backend", slurm),
            patch.object(service, "generate", aquifer),
        ):
            result = await service.generate_feedback(LLM_INPUT)

        self.assertEqual(result, VALID_FEEDBACK)
        aquifer.assert_awaited_once()


def _valid_feedback_json():
    return (
        '{"significance_limitations": [], '
        '"significance_improvements": [], '
        '"outreach_limitations": [], '
        '"outreach_improvements": []}'
    )


if __name__ == "__main__":
    unittest.main()
