import pandas as pd
from pathlib import Path

# Resolve the directory relative to this script
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CSV_PATH = BASE_DIR / "assets" / "ref2014_case_features.csv"

if not CSV_PATH.exists():
    print(f"❌ Error: Could not find the file at {CSV_PATH}")
else:
    # low_memory=False prevents DtypeWarnings
    df = pd.read_csv(CSV_PATH, low_memory=False)

    # 1. Identify all rows that are part of a duplicate set
    # keep=False marks every instance of a duplicate as True
    duplicate_rows = df[df.duplicated(subset=['case_id'], keep=False)]

    # 2. Group them to see which IDs are the most frequent
    duplicate_counts = duplicate_rows['case_id'].value_counts()

    print(f"--- Duplicate ID Analysis ---")
    print(f"Total rows in CSV: {len(df)}")
    print(f"Number of unique IDs that have duplicates: {len(duplicate_counts)}")
    print(f"Total 'extra' rows being filtered: {len(df) - df['case_id'].nunique()}")

    print("\nTop 20 Duplicate IDs and how many times they appear:")
    print(duplicate_counts.head(20))

    # Optional: Save the list to a text file if it's too long to read in console
    # duplicate_counts.to_csv("duplicate_ids_found.csv")
    # print("\nFull list saved to duplicate_ids_found.csv")