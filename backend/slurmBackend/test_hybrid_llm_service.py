import unittest
from unittest.mock import AsyncMock

from app.services.llm_service import LLMService


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

    def generate(self, messages, model_name):
        self.calls.append({"messages": messages, "model_name": model_name})
        if self.error:
            raise self.error
        return self.result


class LLMServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_slurm_result_without_calling_aquifer(self):
        slurm = FakeSlurmBackend(result=VALID_FEEDBACK)
        aquifer = AsyncMock()

        result = await LLMService(slurm, aquifer).generate_feedback(LLM_INPUT)

        self.assertEqual(result, VALID_FEEDBACK)
        aquifer.generate.assert_not_awaited()
        self.assertEqual(slurm.calls[0]["model_name"], "selected/model")

    async def test_falls_back_to_aquifer_on_slurm_timeout(self):
        slurm = FakeSlurmBackend(error=TimeoutError("timed out"))
        aquifer = AsyncMock()
        aquifer.generate.return_value = _valid_feedback_json()

        result = await LLMService(slurm, aquifer).generate_feedback(LLM_INPUT)

        self.assertEqual(result, VALID_FEEDBACK)
        aquifer.generate.assert_awaited_once()

    async def test_falls_back_to_aquifer_on_malformed_slurm_result(self):
        slurm = FakeSlurmBackend(result={"unexpected": "value"})
        aquifer = AsyncMock()
        aquifer.generate.return_value = _valid_feedback_json()

        result = await LLMService(slurm, aquifer).generate_feedback(LLM_INPUT)

        self.assertEqual(result, VALID_FEEDBACK)
        aquifer.generate.assert_awaited_once()


def _valid_feedback_json():
    return (
        '{"significance_limitations": [], '
        '"significance_improvements": [], '
        '"outreach_limitations": [], '
        '"outreach_improvements": []}'
    )


if __name__ == "__main__":
    unittest.main()
