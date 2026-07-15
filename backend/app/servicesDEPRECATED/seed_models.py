import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "app" / "database.db"

def seed_models():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    model1_path = "/dcs/large/u2261259/DCS_ICS_Interface/backend/assets/all-roberta-large-v1_classification_20_per_sentenceRDSTiNRSRrNRcnt_fusiongated_exSngl_True_50eps_lr1e-05"


    # (name, architecture, checkpoint_path, embedding_name, input_dim, use_features, granularity, task)
    models = [
        # (
        #     "Roberta-MIL-Fusion-ALL", "MIL Fusion", "assets/models/roberta_fusion_all_f2.pt", "assets/models/scaler_roberta_fusion_all_f2.joblib", 
        #     "all-roberta-large-v1", 1024, 1, "sentence", "classification"
        # ),
        # (
        #     "Qwen3-4B-full-text-MIL", "MIL", "assets/models/qwen3-4b-full-text-mil_f2.pt", "", "Qwen3-Embedding-4B", 2560, 0, "full_text", "classification"
        # ),
        # (
        #     "Qwen3-4B-sentence-MIL", "MIL", "assets/models/qwen3-4b-sentence-mil_f2.pt", "assets/models/scaler_qwen3-4b-sentence-mil_f2.joblib", "Qwen3-Embedding-4B", 2560, 1, "sentence", "classification"
        # ),
        # (
        #     "Mpnet-MIL-Fusion-ALL", "MIL Fusion", "assets/models/mpnet-fusion-sentence-mil_f2.pt", "assets/models/scaler_mpnet-sentence-mil_f2.joblib", "all-mpnet-base-v2", 768, 1, "sentence", "classification"
        # )
        (
            "RoBERTa-Large-FusionGated",
            "AttentionMIL",
            f"{model1_path}/best_model_fold4.pth",
            "",
            "all-roberta-large-v1",
            1024,
            32,
            128,
            "gated",
            "sentence",
            "classification",
            f"{model1_path}/global_feature_importance.csv",
            f"{model1_path}/case_feature_attention.csv",
            1
        )
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO model_configs 
        (name, architecture, checkpoint_path, scaler_path, embedding_name, 
         input_dim, feature_dim, hidden_dim, fusion_type, input_granularity, task, global_importance_path, case_attribution_path, use_features)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, models)

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    seed_models()
    print("Model configurations seeded successfully.")