import sqlite3
import pandas as pd
import json
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "app" / "database.db"
ATTENTION_DIR = BASE_DIR / "assets" / "sentence_attention"

def normalise_case_id(value):
    if value is None or value == "":
        return ""
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value).strip()

def migrate_ref2014_attentions():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT config_id FROM model_configs WHERE name LIKE '%Roberta-MIL-Fusion-ALL%'")
    res = cursor.fetchone()
    if not res:
        print("No model config found for Roberta-MIL-Fusion-ALL. Please run the model config migration first.")
        return
    config_id = int(res[0])

    for fold_num in range(1, 6):
        file_path = ATTENTION_DIR / f"all_sentences_with_attention_fold_{fold_num}.csv"

        if not file_path.exists():
            print(f"Attention file not found: {file_path}")
            continue
    
        print(f"Processing attention data from: {file_path}")
        df = pd.read_csv(file_path, low_memory=False).fillna(0)

        grouped = df.groupby('Case ID')

        for case_id, group in tqdm(grouped, desc=f"Fold {fold_num}"):

            case_id = normalise_case_id(case_id)

            cursor.execute(
                "SELECT document_id FROM documents WHERE case_id = ? AND ref_year = 2014",
                (case_id,)
            )
            doc_row = cursor.fetchone()
            if not doc_row:
                print(f"Document not found for case_id {case_id} in fold {fold_num}. Skipping.")
                continue
            doc_id = doc_row[0]

            first_row = group.iloc[0]
            score = float(first_row['Prediction'])

            label = "High Impact" if score >= 0.5 else "Low Impact"

            cursor.execute("""
                INSERT INTO inferences (document_id, config_id, score, label) VALUES (?, ?, ?, ?)
            """, (doc_id, config_id, score, label))

            inference_id = cursor.lastrowid

            attention_entries = [
                (inference_id, str(row['Sentence']), float(row['Attention Weight']))
                for _, row in group.iterrows()
            ]

            cursor.executemany('''
                INSERT INTO attentions (inference_id, sentence_text, weight)
                VALUES (?, ?, ?)
            ''', attention_entries)

        conn.commit() 
    conn.close()

if __name__ == "__main__":
    migrate_ref2014_attentions()
