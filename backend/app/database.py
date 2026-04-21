import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    print(f"Initialising database at: {DB_PATH}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,                                    -- original REF case ID
            title TEXT,
            institution TEXT,
            uoa TEXT,
            ref_year INTEGER,                                   -- 2014, 2021 or NULL for new cases
            gpa REAL,                                           -- NULL for new cases
            impact_label INTEGER,                               -- 1 for High, 0 for Low
            raw_text TEXT,
            features_json TEXT,                                 -- Readability GTFs + NER counts
            entities_json TEXT,                                 -- SpaCy NER entity list
            UNIQUE(case_id, ref_year)                          -- Ensure no duplicates for REF cases
        )
    """)
    print("Created 'documents' table.")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_configs (
            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            architecture TEXT,
            checkpoint_path TEXT,
            scaler_path TEXT,
            embedding_name TEXT,
            input_dim INTEGER,
            use_features INTEGER, -- some models (Qwen) do not use features 
            input_granularity TEXT, -- 'sentence' or 'document'
            task TEXT -- 'classification' or 'regression'
        )
    """)
    print("Created 'model_configs' table.")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inferences (
            inference_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            config_id INTEGER NOT NULL,
            score REAL,
            label TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
            FOREIGN KEY (config_id) REFERENCES model_configs(config_id) ON DELETE CASCADE
        )
    """)
    print("Created 'inferences' table.")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attentions (
            attention_id INTEGER PRIMARY KEY AUTOINCREMENT,
            inference_id INTEGER NOT NULL,
            sentence_text TEXT NOT NULL,
            weight REAL NOT NULL,
            FOREIGN KEY (inference_id) REFERENCES inferences(inference_id) ON DELETE CASCADE
        )
    """)
    print("Created 'attentions' table.")

    # TODO: Consider adding indexes

    conn.commit()
    conn.close()
    print("\n Database initialisation complete.")

if __name__ == "__main__":
    init_db()