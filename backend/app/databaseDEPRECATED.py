from pathlib import Path

from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.document import DocumentFeatures, DocumentMetadata
from app.models.inference import Attention, Inference, ModelConfig

DB_PATH = Path(__file__).parent / "database.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    print(f"Initialising database at: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    print("Database initialisation complete.")


def model_to_dict(model):
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def get_model_config(config_id):
    with SessionLocal() as db:
        config = db.get(ModelConfig, int(config_id))
        return model_to_dict(config) if config else None


def list_model_configs():
    with SessionLocal() as db:
        configs = db.scalars(select(ModelConfig).order_by(ModelConfig.config_id)).all()
        return [model_to_dict(config) for config in configs]


__all__ = [
    "Attention",
    "Base",
    "DB_PATH",
    "DocumentFeatures",
    "DocumentMetadata",
    "Inference",
    "ModelConfig",
    "Session",
    "SessionLocal",
    "engine",
    "get_db",
    "get_model_config",
    "init_db",
    "list_model_configs",
]


if __name__ == "__main__":
    init_db()
