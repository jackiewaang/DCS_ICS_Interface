# Cleans document sections, combines them, and splits the result into sentences.

import html
import re

import spacy


class EmbeddingPreprocessor:
    def __init__(self):
        self._nlp = None
    
    # Loads spacy model for sentence preprocessing
    def get_spacy_nlp(self):
        if self._nlp is None:
            self._nlp = spacy.load("en_core_web_sm")
        return self._nlp
    
    def clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", str(text or ""))
        text = html.unescape(text)
        text = re.sub(r"http[s]?://", "", text)
        return text.strip()

    # Combine summary, research, details into single flat text
    def build_full_text(self, summary: str, research: str, details: str) -> str:
        sections = [
            self.clean_text(summary),
            self.clean_text(research),
            self.clean_text(details),
        ]

        return "\n".join(section for section in sections if section)

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
