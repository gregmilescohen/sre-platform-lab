"""Shared SQLAlchemy ORM models for PulseBoard apps."""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from ulid import ULID


def _utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


def _new_ulid() -> str:
    """Return a new ULID string."""
    return str(ULID())


class Base(DeclarativeBase):
    """SQLAlchemy declarative base shared by all PulseBoard apps."""


class EventLog(Base):
    """Immutable record of a single emitted event.

    Written by pulseboard-consumer after reading from the Pub/Sub topic.
    Read by pulseboard-api GET /events for the UI charts.

    IDs are ULIDs — time-sortable, 26-char Crockford base32 strings.
    The Python attribute `event_metadata` maps to the DB column `metadata`
    because `metadata` is reserved by SQLAlchemy's DeclarativeBase.
    """

    __tablename__ = "event_log"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=_new_ulid)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
