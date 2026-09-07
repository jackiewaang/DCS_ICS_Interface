import json
import os
import re
import sys
from pathlib import Path

from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

from slurmBackend.gemma_prompt import build_diagnostic_prompt, build_score_prompt


BASE_MODEL = "google/gemma-3-12b-it"
MODEL_NAME = "Gemma 3 12B fine-tuned"


def generate(llm: LLM, prompt: str, max_tokens: int) -> str:
    tokenizer = llm.get_tokenizer()
    formatted_prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    adapter_path = Path(__file__).resolve().parents[1] / "assets/models/Gemma-3-12B-finetuned"
    outputs = llm.generate(
        [formatted_prompt],
        sampling_params=SamplingParams(temperature=0.0, max_tokens=max_tokens),
        lora_request=LoRARequest("gemma_ref_lora", 1, str(adapter_path)),
    )
    if not outputs or not outputs[0].outputs:
        raise ValueError("Gemma returned no generated output.")
    return outputs[0].outputs[0].text.strip()


def extract_score(text: str) -> float:
    match = re.search(r"(?<![\d.])(?:[0-3](?:\.\d+)?|4(?:\.0+)?)(?![\d.])", text)
    if not match:
        raise ValueError(f"Gemma returned an invalid GPA: {text!r}")
    return float(match.group(0))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: offline_gemma.py <remote_dir>")

    remote_dir = Path(sys.argv[1])
    with (remote_dir / "input.json").open("r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    if not isinstance(payload, dict):
        raise ValueError("input.json must contain a JSON object.")

    summary = str(payload.get("summary", ""))
    research = str(payload.get("research", ""))
    impact = str(payload.get("impact", ""))
    adapter_path = Path(__file__).resolve().parents[1] / "assets/models/Gemma-3-12B-finetuned"
    if not (adapter_path / "adapter_model.safetensors").is_file():
        raise FileNotFoundError(f"Gemma adapter not found at {adapter_path}")

    os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    llm = LLM(
        model=os.getenv("GEMMA_BASE_MODEL", BASE_MODEL),
        dtype="bfloat16",
        max_model_len=int(os.getenv("GEMMA_MAX_MODEL_LEN", "8192")),
        gpu_memory_utilization=float(os.getenv("GEMMA_GPU_MEMORY_UTIL", "0.9")),
        quantization="bitsandbytes",
        load_format="bitsandbytes",
        enable_lora=True,
        max_lora_rank=16,
    )

    raw_score = generate(llm, build_score_prompt(summary, research, impact), max_tokens=20)
    score = extract_score(raw_score)
    comments = generate(
        llm,
        build_diagnostic_prompt(score, summary, research, impact),
        max_tokens=1500,
    )

    output_path = remote_dir / "output.json"
    temporary_output_path = remote_dir / "output.json.tmp"
    with temporary_output_path.open("w", encoding="utf-8") as output_file:
        json.dump(
            {"score": score, "comments": comments, "model_name": MODEL_NAME},
            output_file,
        )
    temporary_output_path.replace(output_path)


if __name__ == "__main__":
    main()
