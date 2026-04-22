import pandas as pd
import json
import os

def generate_model_weights(csv_path, output_path):
    # Load CSV file
    df = pd.read_csv(csv_path)

    # Define GTFs feature categories
    gtfs = [
        "Flesch Reading Ease", "Dale-Chall Readability Score", "SMOG Index", "Automated Readability Index", # Readability
        "Sentiment (mean)", "Sentiment (10th)", "Sentiment (50th)", "Sentiment (75th)", "Sentiment (90th)", # Sentiment
        "Word count", "Paragraph count", # Structure
        "Number of organisations mentioned", "Number of named individuals", "Number of countries or regions mentioned" # Named Entity
    ]

    summary_list = []
    full_text_list = []

    for _, row in df.iterrows():
        name = str(row['Feature'])
        val = float(row['Importance'])

        feature_obj = {"feature": name, "importance": val}

        if name in gtfs:
            summary_list.append(feature_obj)
        else:
            full_text_list.append(feature_obj)

    for lst in [summary_list, full_text_list]:
        if lst:
            max_val = max(item['importance'] for item in lst)
            for item in lst:
                item['ui_width'] = (item['importance'] / max_val) * 100 if max_val > 0 else 0

    js_content = f"""// Auto-generated Weights for REF 2014 Analysis
// SUMMARY_WEIGHTS: Global Textual Features (GTFs) from Summaries/Descriptions
export const SUMMARY_WEIGHTS = {json.dumps(summary_list, indent=2)};

// FULL_TEXT_WEIGHTS: NER Features from Full ICS text pipeline
export const FULL_TEXT_WEIGHTS = {json.dumps(full_text_list, indent=2)};
"""

    with open(output_path, 'w') as f:
        f.write(js_content)

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.abspath(__file__))

    csv_file = os.path.join(base_path, '..', 'assets', 'RandomForest_feature_importance.csv')
    output_file = os.path.join(base_path, '..','data', 'feature_weights.js')

    generate_model_weights(csv_file, output_file)