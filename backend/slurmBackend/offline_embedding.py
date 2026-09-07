import json
import os
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: offline_embedding.py <remote_dir>")

    remote_dir = Path(sys.argv[1])
    input_path = remote_dir / "input.json"
    output_path = remote_dir / "output.json"
    temporary_output_path = remote_dir / "output.json.tmp"

    with input_path.open("r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    if not isinstance(payload, dict):
        raise ValueError("input.json must contain a JSON object.")

    texts = payload.get("texts")
    if not isinstance(texts, list) or not texts:
        raise ValueError("input.json must contain a non-empty 'texts' list.")
    if not all(isinstance(text, str) for text in texts):
        raise ValueError("Every item in 'texts' must be a string.")

    prompt = payload.get("prompt")
    if prompt is not None and not isinstance(prompt, str):
        raise ValueError("'prompt' must be a string or null.")

    model_name = payload.get("model_name")
    if not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("input.json must contain a non-empty 'model_name'.")

    model = SentenceTransformer(
        model_name,
        device="cuda",
        trust_remote_code=True,
    )
    embeddings = model.encode(
        texts,
        prompt=prompt,
        batch_size=int(os.getenv("SLURM_EMBEDDING_BS", "8")),
    ).astype("float32")

    with temporary_output_path.open("w", encoding="utf-8") as output_file:
        json.dump({"embeddings": embeddings.tolist()}, output_file)

    temporary_output_path.replace(output_path)


if __name__ == "__main__":
    main()
