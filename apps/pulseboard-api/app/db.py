"""Database engine, session factory, and ORM base."""

import os
from collections.abc import Generator

from pulseboard_shared.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pulseboard.db")

# SQLAlchemy requires an explicit dialect prefix for PostgreSQL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all database tables (idempotent)."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session]:
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
