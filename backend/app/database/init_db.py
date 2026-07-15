from app.database.seed_inferences import seed_inferences
from app.database.seed_models import seed_models
from app.database.seed_past_cases import seed_past_cases
from app.database.session import DB_PATH, engine
from app.models.base import Base
from sqlalchemy import inspect, text

from app.models import document, inference


def init_db():
    print(f"Initialising database at: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    _ensure_inference_created_at()
    seeded_case_count = seed_past_cases()
    print(f"Seeded {seeded_case_count} past case row(s).")
    seeded_count = seed_models()
    print(f"Seeded {seeded_count} model configuration(s).")
    seeded_inferences = seed_inferences()
    print(f"Seeded inference assets: {seeded_inferences}.")
    print("Database initialisation complete.")


def _ensure_inference_created_at() -> None:
    inspector = inspect(engine)
    if "inferences" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("inferences")}
    with engine.begin() as connection:
        if "created_at" not in columns:
            connection.execute(text("ALTER TABLE inferences ADD COLUMN created_at DATETIME"))
            connection.execute(
                text(
                    """
                    UPDATE inferences
                    SET created_at = CURRENT_TIMESTAMP
                    WHERE created_at IS NULL
                    """
                )
            )

        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS set_inferences_created_at_after_insert
                AFTER INSERT ON inferences
                FOR EACH ROW
                WHEN NEW.created_at IS NULL
                BEGIN
                    UPDATE inferences
                    SET created_at = CURRENT_TIMESTAMP
                    WHERE inference_id = NEW.inference_id;
                END
                """
            )
        )
