from app.database.seed_models import seed_models
from app.database.session import DB_PATH, engine
from app.models.base import Base

from app.models import feedback, model_configs


def init_db():
    if DB_PATH.exists():
        print(f"Database already exists at: {DB_PATH}")
        return

    print(f"Initialising database at: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    seeded_count = seed_models()
    print(f"Seeded {seeded_count} model configuration(s).")
    print("Database initialisation complete.")
