import json
import os
import sys
from pathlib import Path

from app.llm.prompt import build_prompt
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams


REQUIRED_KEYS = {
    "significance_limitations",
    "significance_improvements",
    "outreach_limitations",
    "outreach_improvements",
}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: offline_llm.py <remote_dir>")

    remote_dir = Path(sys.argv[1])
    input_path = remote_dir / "input.json"
    output_path = remote_dir / "output.json"
    temporary_output_path = remote_dir / "output.json.tmp"

    with input_path.open("r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    if not isinstance(payload, dict):
        raise ValueError("input.json must contain a JSON object.")

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        messages = build_prompt(
            prediction=payload["prediction_label"],
            probability=payload.get("score") or 0,
            top_sentences=payload.get("top_sentences", []),
            feature_importances=payload.get("top_features", []),
            summary=payload.get("summary", ""),
            details=payload.get("details", ""),
        )

    model_name = payload.get("model_name")
    if not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("input.json must contain a non-empty 'model_name'.")

    llm = LLM(
        model=model_name,
        max_model_len=int(os.getenv("MAX_MODEL_LEN", "8192")),
        gpu_memory_utilization=float(os.getenv("GPU_MEMORY_UTIL", "0.6")),
        quantization=os.getenv("QUANTIZATION", "bitsandbytes"),
    )
    sampling_params = SamplingParams(
        temperature=0,
        max_tokens=1024,
        structured_outputs=StructuredOutputsParams(json_object=True),
    )

    tokenizer = llm.get_tokenizer()
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    outputs = llm.generate([prompt], sampling_params=sampling_params)
    if not outputs or not outputs[0].outputs:
        raise ValueError("LLM returned no generated output.")

    result_text = outputs[0].outputs[0].text.strip()
    result = json.loads(result_text)

    if not isinstance(result, dict):
        raise ValueError("LLM response must be a JSON object.")
    missing_keys = REQUIRED_KEYS - result.keys()
    if missing_keys:
        raise ValueError(f"LLM response missing keys: {', '.join(sorted(missing_keys))}")

    with temporary_output_path.open("w", encoding="utf-8") as output_file:
        json.dump(result, output_file)

    temporary_output_path.replace(output_path)


if __name__ == "__main__":
    main()
