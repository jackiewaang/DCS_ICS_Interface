from sqlalchemy.orm import DeclarativeBase, registry

class Base(DeclarativeBase):
    registry = registry()
