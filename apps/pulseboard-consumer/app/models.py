"""SQLAlchemy ORM models.

Mirrors the EventLog model from pulseboard-api. The consumer is the sole
writer to event_log; the API reads from it.
"""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from app.db import Base


def _utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


def _new_ulid() -> str:
    """Return a new ULID string."""
    return str(ULID())


class EventLog(Base):
    """Immutable record of a single event received from the Pub/Sub topic."""

    __tablename__ = "event_log"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=_new_ulid)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
