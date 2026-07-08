import os
import re
import html

import spacy
from sentence_transformers import SentenceTransformer


DEFAULT_PROMPTS = {
    "classification2": "Given a text from a research impact report, classify the research impact into high-quality or low-quality: ",
}

MODEL_MAPPING = {
    "all-roberta-large-v1": "sentence-transformers/all-roberta-large-v1",
    "Qwen3-Embedding-4B": "Qwen/Qwen3-Embedding-4B",
    "Qwen-Qwen3-Embedding-4B": "Qwen/Qwen3-Embedding-4B",
}


class EmbedderEngine:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.models = {}
        self._nlp = None

    def get_spacy_nlp(self):
        if self._nlp is None:
            self._nlp = spacy.load("en_core_web_sm")
        return self._nlp

    def get_model(self, model_name: str):
        if model_name not in self.models:
            load_path = MODEL_MAPPING.get(model_name, model_name)
            is_qwen = "qwen" in load_path.lower()
            token = os.getenv("HF_TOKEN") if is_qwen else None

            self.models[model_name] = SentenceTransformer(
                load_path,
                token=token,
                device=self.device,
                trust_remote_code=is_qwen,
            )

        return self.models[model_name]

    def build_full_text(self, summary_text: str, research_text: str, details_text: str) -> str:
        sections = [
            self.clean_text(summary_text),
            self.clean_text(research_text),
            self.clean_text(details_text),
        ]
        return "\n".join(section for section in sections if section)

    def clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", str(text or ""))
        text = html.unescape(text)
        text = re.sub(r"http[s]?://", "", text)
        return text.strip()

    def get_sentences(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        doc = self.get_spacy_nlp()(text)
        return [str(sentence) for sentence in doc.sents]

    def get_prompt(self, prompt_name: str | None = "classification2", prompt: str | None = None) -> str | None:
        if prompt is not None:
            return prompt
        if prompt_name is None:
            return None
        return DEFAULT_PROMPTS.get(prompt_name)

    def encode_inputs(
        self,
        inputs: list[str],
        model_name: str,
        input_type: str,
        prompt_name: str | None = "classification2",
        prompt: str | None = None,
    ) -> list[list[float]]:
        if not inputs:
            return []

        model = self.get_model(model_name)
        batch_size = 8 if input_type in {"sentence", "sentences"} else 1
        encode_prompt = self.get_prompt(prompt_name=prompt_name, prompt=prompt)

        encode_kwargs = {
            "batch_size": batch_size,
            "convert_to_numpy": True,
        }
        if encode_prompt is not None:
            encode_kwargs["prompt"] = encode_prompt

        embeddings = model.encode(inputs, **encode_kwargs)
        return embeddings.tolist()

    def run_embedding_inference(
        self,
        summary_text: str,
        research_text: str,
        details_text: str,
        model_name: str,
        granularity: str,
        prompt_name: str | None = "classification2",
        prompt: str | None = None,
    ) -> tuple[list[str], list[list[float]]]:
        full_text = self.build_full_text(summary_text, research_text, details_text)

        if granularity in {"sentence", "sentences"}:
            inputs = self.get_sentences(full_text)
            input_type = "sentences"
        else:
            inputs = [full_text] if full_text.strip() else []
            input_type = "full_text"

        embeddings = self.encode_inputs(
            inputs=inputs,
            model_name=model_name,
            input_type=input_type,
            prompt_name=prompt_name,
            prompt=prompt,
        )
        return inputs, embeddings


embedder = EmbedderEngine()
