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
        if model_name not in self.models:
            self.models[model_name] = SentenceTransformer(
                model_name,
                device=self.device,
                trust_remote_code=True
            )
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