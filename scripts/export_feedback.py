import csv
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "backend" / "database.db"
OUTPUT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "feedback.csv"


with sqlite3.connect(DB_PATH) as connection:
    rows = connection.execute(
        "SELECT feedback_id, rating, message, created_at "
        "FROM feedback ORDER BY created_at"
    ).fetchall()

with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
    writer = csv.writer(output_file)
    writer.writerow(["feedback_id", "rating", "message", "created_at"])
    writer.writerows(rows)

print(f"Exported {len(rows)} feedback entries to {OUTPUT_PATH}")
