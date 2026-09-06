import asyncio
import logging
import time


logger = logging.getLogger(__name__)


class GemmaService:
    def __init__(self, slurm_client):
        self.slurm_client = slurm_client

    async def run_inference(self, sections: dict, request_id: str) -> dict:
        started_at = time.monotonic()
        logger.info("Dispatching Gemma inference to Slurm request_id=%s", request_id)

        result = await asyncio.to_thread(
            self.slurm_client.run_gemma,
            sections,
        )
        validated_result = self._validate_result(result)
        logger.info(
            "Gemma inference completed request_id=%s elapsed_seconds=%.2f",
            request_id,
            time.monotonic() - started_at,
        )
        return validated_result

    @staticmethod
    def _validate_result(result: object) -> dict:
        if not isinstance(result, dict):
            raise ValueError("Gemma response must be a JSON object.")

        score = result.get("score")
        comments = result.get("comments")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 4:
            raise ValueError("Gemma response must contain a score between 0 and 4.")
        if not isinstance(comments, str) or not comments.strip():
            raise ValueError("Gemma response must contain diagnostic comments.")

        return {
            "score": float(score),
            "comments": comments.strip(),
            "model_name": result.get("model_name", "Gemma 3 12B fine-tuned"),
        }
