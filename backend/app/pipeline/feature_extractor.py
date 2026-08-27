import re
import statistics

import spacy
import textstat
from nltk.sentiment import SentimentIntensityAnalyzer

import nltk
import os

NLTK_DATA = "/springbrook/share/dcsresearch/u2261259/DCS_ICS_Interface/backend/venv/nltk/data"
if NLTK_DATA not in nltk.data.path:
    nltk.data.path.append(NLTK_DATA)

FEATURE_COLUMNS = [
    "Flesch Reading Ease",
    "Dale-Chall Readability Score",
    "SMOG Index",
    "Automated Readability Index",
    "Sentiment (mean)",
    "Sentiment (10th)",
    "Sentiment (50th)",
    "Sentiment (75th)",
    "Sentiment (90th)",
    "Any monetary values mentioned (list them with currency)",
    "Total monetary value",
    "Word count",
    "Paragraph count",
]

SPACY_ENTITY_LABELS = [
    "PERSON",
    "NORP",
    "FAC",
    "ORG",
    "GPE",
    "LOC",
    "PRODUCT",
    "EVENT",
    "WORK_OF_ART",
    "LAW",
    "LANGUAGE",
    "DATE",
    "TIME",
    "PERCENT",
    "MONEY",
    "QUANTITY",
    "ORDINAL",
    "CARDINAL",
]

ENTITY_LISTS_KEY = "entities"


class FeatureExtractorEngine:
    def __init__(self):
        self.nlp_sm = spacy.load("en_core_web_sm")
        if "sentencizer" not in self.nlp_sm.pipe_names:
            self.nlp_sm.add_pipe("sentencizer")
        self.nlp_trf = spacy.load("en_core_web_trf")
        self.sia = SentimentIntensityAnalyzer()

    def estimate_total_monetary_value(self, money_list: list[str]) -> float:
        total = 0

        for item in money_list:
            match = re.search(
                r"([£$€])?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|thousand)?",
                item,
                re.IGNORECASE,
            )

            if match:
                amount = float(match.group(2).replace(",", ""))
                multiplier = match.group(3)

                if multiplier:
                    if "thousand" in multiplier.lower():
                        amount *= 1e3
                    elif "million" in multiplier.lower():
                        amount *= 1e6
                    elif "billion" in multiplier.lower():
                        amount *= 1e9

                total += amount

        if total > 0:
            return round(total, 2)

        return 0

    def build_feature_text(self, summary_text: str, research_text: str, details_text: str) -> str:
        return f"{str(summary_text or '')}\n\n{str(research_text or '')}\n\n{str(details_text or '')}"

    def extract_from_text(self, text: str) -> dict:

        # Remove Excel/XML exports (&#x000D; = carriage return)
        text = re.sub(r'_x000D_', ' ', text, flags=re.IGNORECASE)

        features = {}

        # readability ******************
        features["Flesch Reading Ease"] = textstat.flesch_reading_ease(text)
        features["Dale-Chall Readability Score"] = textstat.dale_chall_readability_score(text)
        features["SMOG Index"] = textstat.smog_index(text)
        features["Automated Readability Index"] = textstat.automated_readability_index(text)

        # sentiment ******************
        doc_sm = self.nlp_sm(text)
        sentences = [sent.text for sent in doc_sm.sents]
        sentiments = [
            self.sia.polarity_scores(sent)["compound"]
            for sent in sentences
        ]

        if len(sentiments) >= 2:
            features["Sentiment (mean)"] = round(statistics.mean(sentiments), 4)
            features["Sentiment (10th)"] = round(statistics.quantiles(sentiments, n=10)[0], 4)
            features["Sentiment (50th)"] = round(statistics.median(sentiments), 4)
            features["Sentiment (75th)"] = round(statistics.quantiles(sentiments, n=4)[2], 4)
            features["Sentiment (90th)"] = round(statistics.quantiles(sentiments, n=10)[8], 4)
        elif len(sentiments) == 1:
            val = round(sentiments[0], 4)
            features["Sentiment (mean)"] = val
            features["Sentiment (10th)"] = val
            features["Sentiment (50th)"] = val
            features["Sentiment (75th)"] = val
            features["Sentiment (90th)"] = val
        else:
            features["Sentiment (mean)"] = 0
            features["Sentiment (10th)"] = 0
            features["Sentiment (50th)"] = 0
            features["Sentiment (75th)"] = 0
            features["Sentiment (90th)"] = 0

        # entities ******************
        orgs = set()
        individuals = set()
        countries_regions = set()
        money_mentions = []

        for ent in doc_sm.ents:
            entity_text = ent.text.strip()
            if not entity_text:
                continue

            if ent.label_ == "ORG":
                orgs.add(entity_text)
            elif ent.label_ == "PERSON":
                individuals.add(entity_text)
            elif ent.label_ in {"GPE", "LOC"}:
                countries_regions.add(entity_text)
            elif ent.label_ == "MONEY":
                money_mentions.append(entity_text)

        features["Number of organizations mentioned"] = len(orgs)
        features["Number of named individuals"] = len(individuals)
        features["Number of countries or regions mentioned"] = len(countries_regions)
        features["Any monetary values mentioned (list them with currency)"] = "; ".join(money_mentions)
        features["Total monetary value"] = self.estimate_total_monetary_value(money_mentions)

        doc_trf = self.nlp_trf(text)
        unique_entities = {label: {} for label in SPACY_ENTITY_LABELS}

        for ent in doc_trf.ents:
            entity_text = ent.text.strip()
            if entity_text and ent.label_ in unique_entities:
                unique_entities[ent.label_].setdefault(
                    entity_text.lower(),
                    entity_text,
                )

        features[ENTITY_LISTS_KEY] = {
            label: list(entities.values())
            for label, entities in unique_entities.items()
        }

        # counts ***********************
        features["Word count"] = len(text.split())

        features["Paragraph count"] = text.count("\n\n") + 1

        return features

    def extract(self, summary_text: str, research_text: str, details_text: str) -> dict:
        text = self.build_feature_text(summary_text, research_text, details_text)
        return self.extract_from_text(text)


feature_extractor = FeatureExtractorEngine()
