import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "app" / "database.db"

def seed_models():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # (name, architecture, checkpoint_path, embedding_name, input_dim, use_features, granularity, task)
    models = [
        (
            "Roberta-MIL-Fusion-ALL", "MIL Fusion", "assets/models/roberta_fusion_all_f2.pt", "assets/models/scaler_roberta_fusion_all_f2.joblib", 
            "all-roberta-large-v1", 1024, 1, "sentence", "classification"
        ),
        (
            "Qwen3-4B-full-text-MIL", "MIL", "assets/models/qwen3-4b-full-text-mil_f2.pt", "", "Qwen3-Embedding-4B", 2560, 0, "full_text", "classification"
        )
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO model_configs 
        (name, architecture, checkpoint_path, scaler_path, embedding_name, 
         input_dim, use_features, input_granularity, task)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, models)

    conn.commit()
    cursor.close()

if __name__ == "__main__":
    seed_models()
    print("Model configurations seeded successfully.")