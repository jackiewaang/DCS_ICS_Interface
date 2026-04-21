import sqlite3
import json
from datetime import datetime

DB_PATH = "app/database.db"

def create_inference_case(filename, features, sentences, prediction, institution, uoa, config_id):
    """
    Saves new inference data into the ref_language database.
    Leaves case_id, ref_year, gpa, and impact_label as NULL for new inferences.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Prepare JSON blobs
        # We separate the highlights (NER) from the statistical metrics (GTFs)
        entities_blob = json.dumps(features.get("highlights", {}))
        
        # Filter out the non-numeric highlight data for the features_json
        stats_only = {k: v for k, v in features.items() if k != "highlights"}
        features_blob = json.dumps(stats_only)
        
        # 2. Insert into 'documents'
        # case_id, ref_year, gpa, and impact_label are omitted (defaulting to NULL)
        cursor.execute("""
            INSERT INTO documents (
                title, institution, uoa, raw_text, 
                features_json, entities_json
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"[Inference] {filename}",
            institution,
            uoa,
            "\n\n".join(sentences),
            features_blob,
            entities_blob
        ))
        
        doc_id = cursor.lastrowid

        # 3. Insert into 'inferences'
        # Label is derived from the threshold (0.5)
        impact_label = "High Impact" if prediction['score'] >= 0.5 else "Low Impact"
        
        cursor.execute("""
            INSERT INTO inferences (
                document_id, config_id, score, label
            ) VALUES (?, ?, ?, ?)
        """, (
            doc_id,
            config_id,
            prediction['score'],
            impact_label
        ))
        
        inf_id = cursor.lastrowid

        # 4. Insert into 'attentions' (Bulk insert for speed)
        # We fill 'inference_id', 'sentence_text', and 'weight'
        att_records = [
            (inf_id, sent, weight)
            for sent, weight in zip(sentences, prediction['attention'])
        ]
        
        cursor.executemany("""
            INSERT INTO attentions (inference_id, sentence_text, weight)
            VALUES (?, ?, ?)
        """, att_records)

        conn.commit()
        return doc_id 

    except Exception as e:
        conn.rollback()
        print(f"DATABASE CRITICAL ERROR: {e}")
        raise e
    finally:
        conn.close()