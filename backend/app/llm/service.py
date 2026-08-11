# Feed saved MIL results to build prompt in prompt.py and call LLM in client.py to generate review feedback for the case study

import json
from json import JSONDecodeError

from app.llm.client import generate
from app.llm.prompt import build_prompt
from app.repositories.inference_repository import (
    get_attention_mil_results_for_llm,
    save_llm_inference_completed,
    save_llm_inference_error,
)


async def generate_review(inference_id):
    inference = get_attention_mil_results_for_llm(inference_id)
    if inference is None:
        raise ValueError(f"Inference {inference_id} was not found.")

    messages = build_prompt(
        prediction=inference["prediction_label"],
        probability=inference["score"] or 0,
        top_sentences=inference["top_sentences"],
        feature_importances=inference["top_features"],
        summary=inference["summary"],
        details=inference["details"],
    )

    try:
        result = await generate(messages)
        print(f"Raw LLM response for inference {inference_id}: {result!r}")
        analysis = _parse_llm_json(result)

        return save_llm_inference_completed(
            inference_id=inference_id,
            significance_limitations=analysis["significance_limitations"],
            significance_improvements=analysis["significance_improvements"],
            outreach_limitations=analysis["outreach_limitations"],
            outreach_improvements=analysis["outreach_improvements"],
        )
    except Exception as exc:
        save_llm_inference_error(inference_id=inference_id, error_message=str(exc))
        raise


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

    if not isinstance(analysis, dict):
        raise ValueError("LLM JSON response must be an object.")

    required_keys = [
        "significance_limitations",
        "significance_improvements",
        "outreach_limitations",
        "outreach_improvements",
    ]
    missing_keys = [key for key in required_keys if key not in analysis]
    if missing_keys:
        raise ValueError(f"LLM JSON response missing keys: {', '.join(missing_keys)}")

    return analysis
