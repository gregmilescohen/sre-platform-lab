"""SQLAlchemy ORM models."""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_ulid() -> str:
    return str(ULID())


class EventLog(Base):
    """Immutable record of a single emitted event.

    Written by pulseboard-consumer after it reads from the Pub/Sub topic.
    Read by pulseboard-api GET /events for the UI charts.

    IDs are ULIDs — time-sortable, 26-char Crockford base32 strings.
    """

    __tablename__ = "event_log"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=_new_ulid)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
