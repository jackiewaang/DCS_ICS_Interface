import json


REQUIRED_KEYS = {
    "significance_limitations",
    "significance_improvements",
    "outreach_limitations",
    "outreach_improvements",
}


def validate_llm_response(result: object) -> dict:
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM returned invalid JSON.") from exc

    if not isinstance(result, dict):
        raise ValueError("LLM response must be a JSON object.")

    missing_keys = sorted(REQUIRED_KEYS - result.keys())
    if missing_keys:
        raise ValueError(f"LLM response missing keys: {', '.join(missing_keys)}")

    return result
