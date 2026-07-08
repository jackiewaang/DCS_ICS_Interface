import torch
from sentence_transformers import SentenceTransformer
import spacy
from typing import List, Tuple, Union
from app.services.utils import get_ref_sections

class EmbeddingModel:
    def __init__(self):
        self.device = "cpu"
        self.models = {}
        self._nlp = None

    def get_spacy_nlp(self):
        if self._nlp is None:
            try:
                self._nlp = spacy.load("en_core_web_trf")
            except:
                self._nlp = spacy.load("en_core_web_sm")
        return self._nlp

    def get_model(self, model_name):
        """
        Dynamically loads models based on their name/identifier.
        Handles the difference between standard RoBERTa and custom Qwen architectures.
        """
        if model_name not in self.models:
            print(f"--- INFO: Loading model '{model_name}' ---")
            
            # 1. Map 'friendly names' to actual paths or HF identifiers
            # Update these paths to where you actually stored the files
            model_mapping = {
                "all-roberta-large-v1": "sentence-transformers/all-roberta-large-v1",
                "Qwen3-Embedding-4B": "qwen/qwen3-embedding-4b"
            }

            # 2. Determine the loading source
            # If the name is in our map, use the path. Otherwise, assume it's a raw HF ID.
            load_path = model_mapping.get(model_name, model_name)

            # 3. Handle Qwen-specific requirements
            # Qwen needs 'trust_remote_code', RoBERTa doesn't care (True won't hurt it)
            is_qwen = "qwen" in model_name.lower()
            
            try:
                self.models[model_name] = SentenceTransformer(
                    load_path,
                    device=self.device,
                    trust_remote_code=True if is_qwen else False
                )
                print(f"--- SUCCESS: {model_name} loaded on {self.device} ---")
                
            except Exception as e:
                print(f"--- ERROR: Failed to load model {model_name} from {load_path} ---")
                raise e

        return self.models[model_name]
    
    def get_sentences(self, text):
        if not text or not text.strip():
            return []
        nlp = self.get_spacy_nlp()
        doc = nlp(text)
        return [str(s).strip() for s in doc.sents if len(str(s).strip()) > 10]

    def run_embedding_inference(self, full_text, model_name, granularity):
        sections = get_ref_sections(full_text)
        corpus_text = sections.get("embedding_text", full_text)

        model = self.get_model(model_name)

        if granularity == "sentence":
            sentences = self.get_sentences(corpus_text)
            if not sentences:
                return [], []

            embeddings = model.encode(
                sentences,
                convert_to_numpy=True,
                batch_size=4
            )
            return sentences, embeddings.tolist()

        else:
            embedding = model.encode(
                corpus_text,
                convert_to_numpy=True
            )
            return [corpus_text], [embedding.tolist()]

embedding_engine = EmbeddingModel()