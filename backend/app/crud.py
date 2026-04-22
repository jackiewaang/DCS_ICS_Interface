import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "app/database.db"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_cases(search_query: str = None, uoa: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    # We change the base to 'inferences' to ensure every analysis run is visible.
    # Joining with 'model_configs' gives us the friendly name of the AI model.
    query = """
        SELECT 
            i.inference_id, 
            d.document_id, 
            d.case_id, 
            d.title, 
            d.institution, 
            d.uoa, 
            d.gpa, 
            i.score as model_prediction, 
            i.label as model_label,
            mc.name as model_name
        FROM inferences i
        JOIN documents d ON i.document_id = d.document_id
        JOIN model_configs mc ON i.config_id = mc.config_id
        WHERE 1=1
    """
    params = []
    
    if search_query:
        # Search across Title, ID, or Institution
        query += " AND (d.title LIKE ? OR d.institution LIKE ? OR d.document_id LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
    
    if uoa:
        query += " AND d.uoa = ?"
        params.append(uoa)
    
    # Order by inference_id so the most recent analysis is always at the top
    query += " ORDER BY i.inference_id DESC"
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def get_inference_details(inference_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            d.*, 
            i.inference_id,
            i.score, 
            i.label, 
            mc.name as model_name,
            mc.input_granularity
        FROM inferences i
        JOIN documents d ON i.document_id = d.document_id
        JOIN model_configs mc ON i.config_id = mc.config_id
        WHERE i.inference_id = ?
    """, (inference_id,))
    
    row = cursor.fetchone()
    conn.close() # Close early since we have the data
    
    if not row:
        return None
    
    case_dict = dict(row)
    
    # --- JSON PARSING (Mandatory for Frontend) ---
    case_dict['features'] = json.loads(case_dict['features_json']) if case_dict.get('features_json') else {}
    case_dict['entities'] = json.loads(case_dict['entities_json']) if case_dict.get('entities_json') else {}
    
    # --- HEATMAP FETCH ---
    case_dict['heatmap'] = get_heatmap_for_inference(inference_id)
    
    return case_dict

def get_heatmap_for_inference(inference_id: int):
    """
    Fetches sentence-level attention weights for a specific model run.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    # We filter strictly by inference_id to get only THIS model's perspective
    cursor.execute("""
        SELECT 
            sentence_text, 
            weight as attention_score 
        FROM attentions 
        WHERE inference_id = ?
    """, (inference_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows # This will be a list of dictionaries

def get_case_by_id(document_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    # 1. Get the Document and its latest Inference
    cursor.execute("""
        SELECT 
            d.*, 
            i.inference_id,
            i.score, 
            i.label, 
            mc.name as model_name
        FROM documents d
        LEFT JOIN inferences i ON d.document_id = i.document_id
        LEFT JOIN model_configs mc ON i.config_id = mc.config_id
        WHERE d.document_id = ?
        ORDER BY i.inference_id DESC LIMIT 1
    """, (document_id,))

    print(f"--- DEBUG: Executed get_case_by_id with document_id={document_id} ---")
    
    row = cursor.fetchone()
    print(row)
    if not row:
        conn.close()
        return None

    case_dict = dict(row)
    
    # 2. Parse the JSON blobs so the frontend gets objects, not strings
    case_dict['features'] = json.loads(case_dict['features_json']) if case_dict['features_json'] else {}
    case_dict['entities'] = json.loads(case_dict['entities_json']) if case_dict['entities_json'] else {}

    # 3. Get the Heatmap (Attentions) linked to that specific inference
    if case_dict['inference_id']:
        cursor.execute("""
            SELECT sentence_text, weight as attention_score 
            FROM attentions 
            WHERE inference_id = ?
        """, (case_dict['inference_id'],))
        attention_rows = cursor.fetchall()
        case_dict['heatmap'] = attention_rows
    else:
        case_dict['heatmap'] = []

    conn.close()
    return case_dict

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
        att_data = prediction.get('attention')
        
        if isinstance(att_data, (list, tuple)) and len(att_data) > 0:
            att_records = [
                (inf_id, sent, weight)
                for sent, weight in zip(sentences, att_data)
            ]
            
            cursor.executemany("""
                INSERT INTO attentions (inference_id, sentence_text, weight)
                VALUES (?, ?, ?)
            """, att_records)
            print(f"--- INFO: Saved {len(att_records)} sentence weights for Heatmap ---")
        else:
            # Full-text model logic: No heatmap to save
            print("--- INFO: Model is Full-Text level. Skipping Attentions table. ---")

        conn.commit()
        return doc_id

    except Exception as e:
        conn.rollback()
        print(f"DATABASE CRITICAL ERROR: {e}")
        raise e
    finally:
        conn.close()