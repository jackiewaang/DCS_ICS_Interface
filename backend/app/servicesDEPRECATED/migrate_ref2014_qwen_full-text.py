import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "app" / "database.db"
QWEN_DIR = BASE_DIR / "assets" / "qwen3-4b-mil-full-text_f2"

def normalise_case_id(value):
    if value is None or value == "":
        return ""
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value).strip()

def migrate_qwen_results():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT config_id FROM model_configs WHERE name = 'Qwen3-4B-full-text-MIL'")
    res = cursor.fetchone()
    if not res:
        print("No model config found for Qwen3-4B-full-text-MIL. Please run the model config migration first.")
        return
    config_id = int(res[0])

    for fold_num in range(1, 6):
        file_path = QWEN_DIR / f"all_sentences_with_attention_fold_{fold_num}.csv"

        if not file_path.exists():
            print(f"Qwen results file not found: {file_path}")
            continue

        print(f"Processing Qwen results from: {file_path}")
        df = pd.read_csv(file_path, low_memory=False).fillna(0)

        unique_cases = df.drop_duplicates(subset=['Case ID'])

        for _, row in tqdm(unique_cases.iterrows(), total=len(unique_cases), desc=f"Fold {fold_num}"):
            clean_case_id = normalise_case_id(row['Case ID'])

            cursor.execute(
                "SELECT document_id FROM documents WHERE case_id = ? AND ref_year = 2014",
                (clean_case_id,)
            )
            doc_row = cursor.fetchone()

            if doc_row:
                doc_id = doc_row[0]
                score = float(row['Prediction'])
                label = "High Impact" if score >= 0.5 else "Low Impact"

                cursor.execute("""
                    INSERT INTO inferences (document_id, config_id, score, label) VALUES (?, ?, ?, ?)
                """, (doc_id, config_id, score, label))
        conn.commit()

    conn.close()

if __name__ == "__main__":
    migrate_qwen_results()
    print("Qwen results migrated successfully.")
