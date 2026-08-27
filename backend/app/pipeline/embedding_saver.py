# Persists generated sentence embeddings and their model metadata as pickle artifacts.

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "embeddings"


class EmbeddingSaver:
    def __init__(self, output_dir: Path = DEFAULT_OUTPUT_DIR):
        self.output_dir = output_dir

    def save(
        self,
        sentences: list[str],
        embeddings: list[list[float]],
        model_config: dict[str, Any],
        sections: dict[str, str],
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        filename_parts = [
            "embeddings",
            timestamp,
            self._filename_part(model_config.get("name") or model_config.get("embedding_name")),
        ]
        source_filename = sections.get("title")
        if source_filename:
            filename_parts.append(self._filename_part(Path(source_filename).stem))

        output_path = self.output_dir / f"{'_'.join(filename_parts)}.pkl"
        output_df = pd.DataFrame(
            {
                "input": sentences,
                "embeddings": embeddings,
            }
        )
        output_df["config_id"] = model_config.get("config_id")
        output_df["embedding_name"] = model_config.get("embedding_name")
        output_df["input_granularity"] = model_config.get("input_granularity")
        output_df.to_pickle(output_path)
        return output_path

    def _filename_part(self, value: Any) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9]+", "-", str(value or "").strip())
        return cleaned.strip("-") or "unknown"
