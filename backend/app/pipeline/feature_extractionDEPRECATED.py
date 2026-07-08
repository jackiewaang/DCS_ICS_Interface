import re
import statistics
import textstat
import html
import spacy
import torch
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk import sent_tokenize
from typing import Dict, List, Tuple

try:
    nlp = spacy.load("en_core_web_trf")
except:
    nlp = spacy.load("en_core_web_sm")

sia = SentimentIntensityAnalyzer()

GTF_ORDER = [
    "Flesch Reading Ease", "Dale-Chall Readability Score", "SMOG Index", "Automated Readability Index",
    "Sentiment (mean)", "Sentiment (10th)", "Sentiment (50th)", "Sentiment (75th)", "Sentiment (90th)",
    "Number of organizations mentioned", "Number of named individuals", "Number of countries or regions mentioned",
    "Word count", "Paragraph count",
    'PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT',
    'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY',
    'QUANTITY', 'ORDINAL', 'CARDINAL'
]

def clean_text(text):

    text = html.unescape(text)
    text = text.replace('\\n', '\n').replace("\\'", "'").replace("`", "'")

    # Punctuation and Number formatting
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])(?=[^\s.,;:!?])', r'\1 ', text)
    text = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', text)
    text = re.sub(r'(\d),\s+(\d{3})', r'\1,\2', text)
    text = re.sub(r'\b(e|i)\s*\.\s*(g|e)\b', r'\1.\2', text)

    # Paragraph preservation logic (The "Buffer" version)
    lines = text.split('\n')
    cleaned_lines = []
    buffer = ''
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                cleaned_lines.append(buffer.strip())
                buffer = ''
            cleaned_lines.append('') # CRITICAL for paragraph count (\n\n)
        elif re.match(r'^[\W_]*$', stripped):
            continue
        else:
            if buffer and not buffer.endswith(('.', ':', '?', '!', '"')):
                buffer += ' ' + stripped
            else:
                if buffer:
                    cleaned_lines.append(buffer.strip())
                buffer = stripped
    if buffer:
        cleaned_lines.append(buffer.strip())
    
    text = '\n'.join(cleaned_lines)

    # Cleanup mid-sentence breaks
    text = re.sub(r'([a-z0-9.,;:])\n(?=[a-z])', r'\1 ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def clean_currency_string(value):
    """EXACT training code logic for monetary floats."""
    if not isinstance(value, str):
        return value
    # Remove £, $, commas, and whitespace
    clean_val = re.sub(r'[£$,\s]', '', value)
    
    multiplier = 1
    if 'billion' in clean_val.lower():
        multiplier = 1_000_000_000
        clean_val = re.sub(r'billion', '', clean_val, flags=re.IGNORECASE)
    elif 'million' in clean_val.lower():
        multiplier = 1_000_000
        clean_val = re.sub(r'million', '', clean_val, flags=re.IGNORECASE)
    elif 'thousand' in clean_val.lower(): # Added thousand to match your earlier helper
        multiplier = 1_000
        clean_val = re.sub(r'thousand', '', clean_val, flags=re.IGNORECASE)
    elif clean_val.lower().endswith('k'): # Added k to catch the 265k/184k
        multiplier = 1_000
        clean_val = clean_val[:-1]
        
    try:
        return float(clean_val) * multiplier
    except ValueError:
        return 0.0

def run_extraction(text: str) -> Tuple[Dict, List[float]]:
    """
    Returns:
    1. A dictionary for the Frontend (with strings and lists)
    2. A flat list of 33 floats in the exact order the Scaler expects.
    """

    # Initialise all features
    feats = {cat: 0 for cat in GTF_ORDER}
    
    # Readability features
    feats["Flesch Reading Ease"] = textstat.flesch_reading_ease(text)
    feats["Dale-Chall Readability Score"] = textstat.dale_chall_readability_score(text)
    feats["SMOG Index"] = textstat.smog_index(text)
    feats["Automated Readability Index"] = textstat.automated_readability_index(text)

    # Sentiment features
    sentences = sent_tokenize(text)
    sentiments = [sia.polarity_scores(s)["compound"] for s in sentences]
    if sentiments:
        feats["Sentiment (mean)"] = round(statistics.mean(sentiments), 4)
        feats["Sentiment (10th)"] = round(statistics.quantiles(sentiments, n=10)[0], 4)
        feats["Sentiment (50th)"] = round(statistics.median(sentiments), 4)
        feats["Sentiment (75th)"] = round(statistics.quantiles(sentiments, n=4)[2], 4)
        feats["Sentiment (90th)"] = round(statistics.quantiles(sentiments, n=10)[8], 4)

    # NER feature extraction
    doc = nlp(text)

    unique_entities = {etype: set() for etype in [
        'PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT',
        'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY',
        'QUANTITY', 'ORDINAL', 'CARDINAL'
    ]}

    for ent in doc.ents:
        if ent.label_ in unique_entities:
            unique_entities[ent.label_].add(ent.text.lower())
    
    for etype, ent_set in unique_entities.items():
        feats[etype] = len(ent_set)

    feats["Number of organizations mentioned"] = feats['ORG']
    feats["Number of named individuals"] = feats['PERSON']
    feats["Number of countries or regions mentioned"] = feats['GPE']
    
    # money_list = [ent.text for ent in doc.ents if ent.label_ == "MONEY"]
    # total_money = 0.0
    # for m in money_list:
    #     total_money += clean_currency_string(m)
    
    # feats["Total monetary value"] = total_money

    feats["Word count"] = len(text.split())
    feats["Paragraph count"] = text.count('\n\n') + 1

    # Create the ordered list for the Scaler
    ordered_list = [float(feats[key]) for key in GTF_ORDER]
    
    ui_data = feats.copy()
    ui_data["highlights"] = {
        "orgs": list(unique_entities['ORG']),
        "people": list(unique_entities['PERSON']),
        "money": list(unique_entities['MONEY']),
    }

    return ui_data, ordered_list