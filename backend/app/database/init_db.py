from app.database.seed_inferences import seed_inferences
from app.database.seed_models import seed_models
from app.database.seed_past_cases import seed_past_cases
from app.database.session import DB_PATH, engine
from app.models.base import Base

from app.models import document, inference


def init_db():
    if DB_PATH.exists():
        print(f"Database already exists at: {DB_PATH}")
        return

    print(f"Initialising database at: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    seeded_case_count = seed_past_cases()
    print(f"Seeded {seeded_case_count} past case row(s).")
    seeded_count = seed_models()
    print(f"Seeded {seeded_count} model configuration(s).")
    seeded_inferences = seed_inferences()
    print(f"Seeded inference assets: {seeded_inferences}.")
    print("Database initialisation complete.")
