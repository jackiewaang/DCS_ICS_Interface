import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.document import DocumentFeatures, DocumentMetadata


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ASSETS_ROOT = BACKEND_ROOT / "assets"

FEATURE_FILES = {
    2014: ASSETS_ROOT / "REF2014" / "case_study_features.csv",
    2021: ASSETS_ROOT / "REF2021" / "case_study_features.csv",
}

ENTITY_FILES = {
    2014: ASSETS_ROOT / "REF2014" / "REF2014_ALL-SpaCy_NER_output_dict-en_core_web_sm.npy",
    2021: ASSETS_ROOT / "REF2021" / "REF2021_ALL-SpaCy_NER_output_dict-en_core_web_sm.npy",
}

METADATA_COLUMNS = {
    "institution",
    "ukprn",
    "region",
    "uoa_id",
    "uoa_name",
    "case_id",
    "case_title",
    "panel",
    "gpa_score",
    "binary_impact_label",
    "region_code",
}

FEATURE_COLUMN_MAP = {
    "Flesch Reading Ease": "flesch_reading_ease",
    "Dale-Chall Readability Score": "dale_chall_readability_score",
    "SMOG Index": "smog_index",
    "Automated Readability Index": "automated_readability_index",
    "Sentiment (mean)": "sentiment_mean",
    "Sentiment (10th)": "sentiment_10th",
    "Sentiment (50th)": "sentiment_50th",
    "Sentiment (75th)": "sentiment_75th",
    "Sentiment (90th)": "sentiment_90th",
    "Word count": "word_count",
    "Paragraph count": "paragraph_count",
}

ENTITY_COLUMN_MAP = {
    "PERSON": "person_entities",
    "NORP": "norp_entities",
    "FAC": "fac_entities",
    "ORG": "org_entities",
    "GPE": "gpe_entities",
    "LOC": "loc_entities",
    "PRODUCT": "product_entities",
    "EVENT": "event_entities",
    "WORK_OF_ART": "work_of_art_entities",
    "LAW": "law_entities",
    "LANGUAGE": "language_entities",
    "DATE": "date_entities",
    "TIME": "time_entities",
    "PERCENT": "percent_entities",
    "MONEY": "money_entities",
    "QUANTITY": "quantity_entities",
    "ORDINAL": "ordinal_entities",
    "CARDINAL": "cardinal_entities",
}


def seed_past_cases(
    db: Session | None = None,
    feature_files: dict[int, Path] = FEATURE_FILES,
    entity_files: dict[int, Path] = ENTITY_FILES,
) -> int:
    """
    Upsert past REF case metadata and handcrafted features.

    The source feature CSVs do not include narrative text, so raw_text,
    summary_text, research_text, and impact_text are intentionally left empty.
    GPA and impact labels are also left empty for now.
    """
    owns_session = db is None
    db = db or SessionLocal()

    try:
        seeded_count = 0
        for ref_year, csv_path in sorted(feature_files.items()):
            entities_by_case_id = _load_entities(entity_files.get(ref_year))
            seeded_count += _seed_feature_file(db, ref_year, csv_path, entities_by_case_id)

        if owns_session:
            db.commit()

        return seeded_count
    except Exception:
        if owns_session:
            db.rollback()
        raise
    finally:
        if owns_session:
            db.close()


def _seed_feature_file(
    db: Session,
    ref_year: int,
    csv_path: Path,
    entities_by_case_id: dict[str, dict[str, list[str]]],
) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"Past case feature file not found: {csv_path}")

    seeded_count = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            case_id = _normalise_case_id(row.get("case_id"))
            if not case_id:
                continue

            document = _get_or_create_document(db, ref_year, case_id)
            document.ref_year = ref_year
            document.case_id = case_id
            document.title = _clean_string(row.get("case_title"))
            document.institution = _clean_string(row.get("institution"))
            document.uoa = _clean_string(row.get("uoa_name"))
            document.status = "past"
            document.gpa = None
            document.impact_label = None
            document.raw_text = None
            document.summary_text = None
            document.research_text = None
            document.impact_text = None

            entities = entities_by_case_id.get(case_id)
            _upsert_features(document, row, entities or {})
            seeded_count += 1

    return seeded_count


def _get_or_create_document(
    db: Session,
    ref_year: int,
    case_id: str,
) -> DocumentMetadata:
    document = db.scalar(
        select(DocumentMetadata).where(
            DocumentMetadata.ref_year == ref_year,
            DocumentMetadata.case_id == case_id,
        )
    )
    if document is not None:
        return document

    document = DocumentMetadata(ref_year=ref_year, case_id=case_id)
    db.add(document)
    return document


def _upsert_features(
    document: DocumentMetadata,
    row: dict[str, Any],
    entities: dict[str, list[str]],
) -> None:
    features = document.features
    if features is None:
        features = DocumentFeatures()
        document.features = features

    feature_values = {
        column: value
        for column, value in row.items()
        if column not in METADATA_COLUMNS and value not in (None, "")
    }
    features.features_json = json.dumps(feature_values)
    normalised_entities = _normalise_entities(entities)
    features.entities_json = json.dumps(normalised_entities)

    for csv_column, model_attribute in FEATURE_COLUMN_MAP.items():
        setattr(features, model_attribute, _safe_float(row.get(csv_column), default=None))

    for entity_label, model_attribute in ENTITY_COLUMN_MAP.items():
        setattr(features, model_attribute, normalised_entities.get(entity_label, []))


def _load_entities(entity_path: Path | None) -> dict[str, dict[str, list[str]]]:
    if entity_path is None or not entity_path.exists():
        return {}

    entity_data = np.load(entity_path, allow_pickle=True).item()
    return {
        _normalise_case_id(case_id): _normalise_entities(entities)
        for case_id, entities in entity_data.items()
    }


def _normalise_entities(entities: Any) -> dict[str, list[str]]:
    if not isinstance(entities, dict):
        return {label: [] for label in ENTITY_COLUMN_MAP}

    return {
        label: _normalise_entity_list(entities.get(label))
        for label in ENTITY_COLUMN_MAP
    }


def _normalise_entity_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    try:
        return [str(item) for item in value if item not in (None, "")]
    except TypeError:
        return [str(value)]


def _normalise_case_id(value: Any) -> str:
    if value in (None, ""):
        return ""
    numeric_case_id = _safe_int(value)
    if numeric_case_id is not None:
        return str(numeric_case_id)
    return str(value).strip()


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _clean_string(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip() or None


if __name__ == "__main__":
    count = seed_past_cases()
    print(f"Seeded {count} past case row(s).")
