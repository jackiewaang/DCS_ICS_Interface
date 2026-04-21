import sqlite3
import pandas as pd
import numpy as np
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "app" / "database.db"
CSV_PATH = BASE_DIR / "assets" / "ref2014_case_features.csv"
NER_PATH = BASE_DIR / "assets" / "ref2014_spacy_ner.npy"

def migrate_ref2014():
    if not CSV_PATH.exists():
        print(f"CSV file not found at {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    ner_entities = {}
    if NER_PATH.exists():
        ner_entities = np.load(str(NER_PATH), allow_pickle=True).item()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print(f"Processing {len(df)} cases...")

    for _, row in df.iterrows():
        og_case_id = int(row['case_id'])
        impact_label = 1 if str(row.get('binary_impact_label')).lower() in ['high'] else 0

        features = {
            "flesch_reading_ease": float(row.get("Flesch Reading Ease", 0)),
            "dale_chall_score": float(row.get("Dale-Chall Readability Score", 0)),
            "smog_index": float(row.get("SMOG Index", 0)),
            "ari": float(row.get("Automated Readability Index", 0)),
            "word_count": int(row.get("Word count", 0)),
            "org_count": int(row.get("Number of organizations mentioned", 0)),
            "money_value": str(row.get("Total monetary value", 0)),
            "person_count": int(row.get("Number of named individuals", 0)),
            "geo_count": int(row.get("Number of countries or regions mentioned", 0)),
            "sentiment_mean": float(row.get("Sentiment (mean)", 0))
        }

        entities = ner_entities.get(str(og_case_id), {}) or ner_entities.get(og_case_id, {})

        cursor.execute("""
            INSERT OR REPLACE INTO documents
            (case_id, title, institution, uoa, ref_year, gpa, impact_label, raw_text, features_json, entities_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            og_case_id,
            row.get('case_title'),
            row.get('institution'),
            row.get('uoa_name'),
            2014,
            float(row.get('gpa_score', 0)),
            impact_label,
            "", 
            json.dumps(features),
            json.dumps(entities)
        ))

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate_ref2014()