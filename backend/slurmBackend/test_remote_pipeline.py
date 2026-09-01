import argparse
import json

from slurmBackend.backend import EmbeddingJobRequest, SlurmBackend
from slurmBackend.config import SlurmConfig
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedding-model", default="Qwen/Qwen3-Embedding-4B")
    parser.add_argument("--llm-model", default="Qwen/Qwen3-4B-Instruct-2507")
    args = parser.parse_args()

    config = SlurmConfig.from_env()
    print(config)
    backend = SlurmBackend(SlurmConfig.from_env())
    

    embeddings = backend.run_embedding(
        EmbeddingJobRequest(
            texts=["This research produced substantial public benefit."],
            model_name=args.embedding_model,
            prompt="Classify the quality of this research impact: ",
        )
    )
    print("Embedding result:", json.dumps(embeddings))

    feedback = backend.run_llm(
        {
            "prediction_label": "high-quality",
            "score": 0.85,
            "top_sentences": [
                {"sentence_text": "The research improved public services.", "weight": 0.9}
            ],
            "top_features": [],
            "summary": "Research with measurable public benefit.",
            "details": "The work was adopted by several public organisations.",
        },
        model_name=args.llm_model,
    )
    print("LLM result:", json.dumps(feedback, indent=2))


if __name__ == "__main__":
    main()
