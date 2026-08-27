# Combines the already-cleaned document sections and splits them into sentences.

import spacy


class EmbeddingPreprocessor:
    def __init__(self):
        self._nlp = None
    
    # Loads spacy model for sentence preprocessing
    def get_spacy_nlp(self):
        if self._nlp is None:
            self._nlp = spacy.load("en_core_web_sm")
        return self._nlp
    
    def build_full_text(self, summary: str, research: str, details: str) -> str:
        return "\n".join(
            str(section or "")
            for section in (summary, research, details)
        )

    # Split text into sentences using spacy
    def get_sentences(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        
        nlp = self.get_spacy_nlp()
        doc = nlp(text)
        return [str(sentence) for sentence in doc.sents]
    
    # Main function to preprocess text into sentences for embedding
    def prepare_sentences(self, summary: str, research: str, details: str) -> list[str]:
        full_text = self.build_full_text(summary, research, details)
        sentences = self.get_sentences(full_text)
        return sentences
