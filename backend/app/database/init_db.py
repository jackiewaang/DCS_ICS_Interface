from app.database.seed_models import seed_models
from app.database.session import DB_PATH, engine
from app.models.base import Base

from app.models import document, inference


SQLITE_SCHEMA_UPGRADES = {
    "document_features": {
        "features_json": "TEXT",
        "entities_json": "TEXT",
    },
}


def init_db():
    print(f"Initialising database at: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_schema_upgrades()
    seeded_count = seed_models()
    print(f"Seeded {seeded_count} model configuration(s).")
    print("Database initialisation complete.")


def _apply_sqlite_schema_upgrades() -> None:
    with engine.begin() as connection:
        for table_name, columns in SQLITE_SCHEMA_UPGRADES.items():
            existing_columns = {
                row[1]
                for row in connection.exec_driver_sql(f"PRAGMA table_info({table_name})")
            }

            for column_name, column_type in columns.items():
                if column_name in existing_columns:
                    continue

                print(f"Adding missing column {table_name}.{column_name}")
                connection.exec_driver_sql(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                )
