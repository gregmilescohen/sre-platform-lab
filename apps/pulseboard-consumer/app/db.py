"""Database engine, session factory, and base model class.

Identical pattern to pulseboard-api. The consumer uses the same database
and writes to the event_log table created by the API on startup.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pulseboard-consumer.db")

# SQLAlchemy requires an explicit dialect prefix for PostgreSQL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


def create_tables() -> None:
    """Create all tables in the database (idempotent)."""
    from app.models import EventLog  # noqa: F401 — imported to register with metadata

    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Return a new SQLAlchemy session."""
    return SessionLocal()
