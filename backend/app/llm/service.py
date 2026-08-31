# Build the review prompt from client-supplied MIL results and call the LLM.

import json
from json import JSONDecodeError

from app.llm.client import generate
from app.llm.prompt import build_prompt


async def generate_feedback(llm_input: dict) -> dict:
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
