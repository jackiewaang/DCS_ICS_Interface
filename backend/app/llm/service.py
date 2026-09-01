# Generate review feedback through Slurm, falling back to Aquifer when needed.

import asyncio
import json
import logging
import os
from json import JSONDecodeError

from app.llm.client import generate
from app.llm.prompt import build_prompt
from slurmBackend.backend import SlurmBackend
from slurmBackend.config import SlurmConfig


logger = logging.getLogger(__name__)

DEFAULT_LLM_MODEL = "Qwen/Qwen3-4B-Instruct-2507"
REQUIRED_KEYS = {
    "significance_limitations",
    "significance_improvements",
    "outreach_limitations",
    "outreach_improvements",
}
slurm_backend = SlurmBackend(SlurmConfig.from_env())


async def generate_feedback(llm_input: dict) -> dict:
    model_name = (
        llm_input.get("model_name")
        or os.getenv("SLURM_LLM_MODEL")
        or os.getenv("LLM_MODEL_NAME")
        or DEFAULT_LLM_MODEL
    )

    try:
        result = await asyncio.to_thread(
            slurm_backend.run_llm,
            llm_input,
            model_name,
        )
        return _validate_llm_analysis(result)
    except Exception:
        logger.warning(
            "Slurm LLM inference failed; falling back to Aquifer",
            exc_info=True,
        )

    messages = build_prompt(
        prediction=llm_input["prediction_label"],
        probability=llm_input.get("score") or 0,
        top_sentences=llm_input.get("top_sentences", []),
        feature_importances=llm_input.get("top_features", []),
        summary=llm_input.get("summary", ""),
        details=llm_input.get("details", ""),
    )
    return _parse_llm_json(await generate(messages))


def _parse_llm_json(result: str | None) -> dict:
    if not result:
        raise ValueError("LLM returned an empty response.")

    try:
        analysis = json.loads(result)
    except JSONDecodeError as exc:
        start = max(exc.pos - 160, 0)
        end = min(exc.pos + 160, len(result))
        snippet = result[start:end].replace("\n", "\\n")
        raise ValueError(
            f"LLM returned invalid JSON at char {exc.pos}: {exc.msg}. "
            f"Nearby output: {snippet!r}"
        ) from exc

    return _validate_llm_analysis(analysis)


def _validate_llm_analysis(analysis: object) -> dict:
    if not isinstance(analysis, dict):
        raise ValueError("LLM JSON response must be an object.")

    missing_keys = sorted(REQUIRED_KEYS - analysis.keys())
    if missing_keys:
        raise ValueError(f"LLM JSON response missing keys: {', '.join(missing_keys)}")

    return analysis
