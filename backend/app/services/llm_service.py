import asyncio
import logging

from app.llm.prompt import build_prompt
from app.llm.validation import validate_llm_response


logger = logging.getLogger(__name__)
DEFAULT_LLM_MODEL = "Qwen/Qwen3-4B-Instruct-2507"


class LLMService:
    def __init__(self, slurm_client, aquifer_client):
        self.slurm_client = slurm_client
        self.aquifer_client = aquifer_client

    async def generate_feedback(self, llm_input: dict) -> dict:
        model_name = llm_input.get("model_name") or DEFAULT_LLM_MODEL
        messages = build_prompt(
            prediction=llm_input["prediction_label"],
            probability=llm_input.get("score") or 0,
            top_sentences=llm_input.get("top_sentences", []),
            feature_importances=llm_input.get("top_features", []),
            summary=llm_input.get("summary", ""),
            details=llm_input.get("details", ""),
        )

        try:
            result = await asyncio.to_thread(
                self.slurm_client.generate,
                messages=messages,
                model_name=model_name,
            )
            return validate_llm_response(result)
        except Exception:
            logger.warning(
                "Slurm LLM failed; falling back to Aquifer",
                exc_info=True,
            )

        result = await self.aquifer_client.generate(messages=messages)
        return validate_llm_response(result)
