import asyncio
import logging
import time
from uuid import uuid4

from app.llm.prompt import build_prompt
from app.llm.validation import validate_llm_response


logger = logging.getLogger(__name__)
DEFAULT_LLM_MODEL = "Qwen/Qwen3-4B-Instruct-2507"


class LLMService:
    def __init__(self, slurm_client, aquifer_client):
        self.slurm_client = slurm_client
        self.aquifer_client = aquifer_client

    async def generate_feedback(
        self,
        llm_input: dict,
        request_id: str | None = None,
    ) -> dict:
        request_id = request_id or str(uuid4())
        model_name = llm_input.get("model_name") or DEFAULT_LLM_MODEL
        logger.info(
            "Building LLM feedback prompt request_id=%s model=%s",
            request_id,
            model_name,
        )
        messages = build_prompt(
            prediction=llm_input["prediction_label"],
            probability=llm_input.get("score") or 0,
            top_sentences=llm_input.get("top_sentences", []),
            feature_importances=llm_input.get("top_features", []),
            summary=llm_input.get("summary", ""),
            details=llm_input.get("details", ""),
        )

        slurm_started_at = time.monotonic()
        logger.info(
            "Dispatching LLM feedback to Slurm request_id=%s model=%s message_count=%d",
            request_id,
            model_name,
            len(messages),
        )
        try:
            result = await asyncio.to_thread(
                self.slurm_client.generate,
                messages=messages,
                model_name=model_name,
            )
            validated_result = validate_llm_response(result)
            logger.info(
                "Slurm LLM feedback validated request_id=%s model=%s elapsed_seconds=%.2f result_keys=%s",
                request_id,
                model_name,
                time.monotonic() - slurm_started_at,
                sorted(validated_result.keys()),
            )
            return validated_result
        except Exception as exc:
            logger.warning(
                "Slurm LLM failed; falling back to Aquifer request_id=%s model=%s elapsed_seconds=%.2f error_type=%s error=%s",
                request_id,
                model_name,
                time.monotonic() - slurm_started_at,
                type(exc).__name__,
                exc,
                exc_info=True,
            )

        aquifer_started_at = time.monotonic()
        logger.info("Dispatching LLM feedback to Aquifer request_id=%s", request_id)
        result = await self.aquifer_client.generate(messages=messages)
        validated_result = validate_llm_response(result)
        logger.info(
            "Aquifer LLM feedback validated request_id=%s elapsed_seconds=%.2f result_keys=%s",
            request_id,
            time.monotonic() - aquifer_started_at,
            sorted(validated_result.keys()),
        )
        return validated_result
