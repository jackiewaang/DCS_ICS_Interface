import sqlite3
import pandas as pd
import json
from pathlib import Path

BASE_DIR = "/dcs/large/u2261259/DCS_ICS_Interface/backend"
DB_PATH = f"{BASE_DIR}/app/database.db"

model_inferences = [
    {
        "name": "RoBERTa-Large-FusionGated",
        "preds_path": f"{BASE_DIR}/assets/all-roberta-large-v1_classification_20_per_sentenceRDSTiNRSRrNRcnt_fusiongated_exSngl_True_50eps_lr1e-05/predictions.csv",
        "sentence_attn_path": f"{BASE_DIR}/assets/all-roberta-large-v1_classification_20_per_sentenceRDSTiNRSRrNRcnt_fusiongated_exSngl_True_50eps_lr1e-05/sentence_attention.csv",
        "feature_attn_path": f"{BASE_DIR}/assets/all-roberta-large-v1_classification_20_per_sentenceRDSTiNRSRrNRcnt_fusiongated_exSngl_True_50eps_lr1e-05/case_feature_attention.csv"
    }
]

def get_document_id(cursor, case_study_id):
    clean_id = int(case_study_id)
    cursor.execute("SELECT document_id FROM documents WHERE case_id = ?", (clean_id,))
    row = cursor.fetchone()
    return row[0] if row else None

def seed_inferences():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for model_info in model_inferences:

        # Get model config ID
        cursor.execute("SELECT config_id FROM model_configs WHERE name = ?", (model_info["name"],))
        row = cursor.fetchone()
        if not row:
            print(f"Skipping {model_info['name']}: Not found in model_configs.")
            continue
        config_id = row[0]

        # Load dataframes
        df_preds = pd.read_csv(model_info["preds_path"])
        df_sent_attn = pd.read_csv(model_info['sentence_attn_path'])
        df_feat_attn = pd.read_csv(model_info['feature_attn_path'])

        # Iterate through predictions and insert inferences
        for _, pred_row in df_preds.iterrows():
            case_id = pred_row['CaseStudyId']

            doc_id = get_document_id(cursor, case_id)
            
            feat_row_all = df_feat_attn[df_feat_attn['CaseStudyId'] == case_id]
            feat_row = feat_row_all.iloc[0]

            abs_attr = {k: v for k, v in feat_row.items() if k.endswith('_AbsAttribution')}

            pred_label = "High" if pred_row['Prediction'] >= 0.5 else "Low"

            cursor.execute("""
                INSERT INTO inferences (
                    document_id, config_id, score, true_label, prediction_label,
                    narrative_contribution, feature_contribution, feature_attributions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                config_id,
                pred_row['Prediction'],
                pred_row['TrueScore'],
                pred_label,
                feat_row.get('LLMBranchContribution', 1.0),
                feat_row.get('HandcraftedBranchContribution', 0.0),
                json.dumps(abs_attr)
            ))

            inference_id = cursor.lastrowid

            case_sentences = df_sent_attn[df_sent_attn['CaseStudyId'] == case_id]

            sentence_batch = []
            sentence_batch = [
                (inference_id, str(sent_row['Sentence']), sent_row['SentenceAttention'])
                for _, sent_row in case_sentences.iterrows()
            ]

            cursor.executemany("""
                INSERT INTO attentions (inference_id, sentence_text, weight)
                VALUES (?, ?, ?)
            """, sentence_batch)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_inferences()
    print("Inferences seeded successfully.")