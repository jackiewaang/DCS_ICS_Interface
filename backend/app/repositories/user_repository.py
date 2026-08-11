from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User

def get_by_username(username: str) -> User | None:
    with SessionLocal() as db:
        return db.scalar(
            select(User).where(User.username == username)
        )