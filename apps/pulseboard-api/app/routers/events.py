"""Events router.

POST /events   Publish an event to the Pub/Sub topic (pulseboard-consumer writes to event_log)
GET  /events   Read time-bucketed event counts from event_log for the UI charts
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from google.cloud import pubsub_v1
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import EventLog
from app.pubsub import get_publisher, publish_event
from app.schemas import DataPoint, EmitRequest, EmitResponse, EventDataResponse

router = APIRouter()

_VALID_BUCKETS = {"minute", "hour"}


def _truncate(dt: datetime, bucket: str) -> datetime:
    """Truncate a datetime to the start of a minute or hour bucket."""
    if bucket == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    return dt.replace(second=0, microsecond=0)


def _bucket_events(events: list[EventLog], bucket: str) -> list[DataPoint]:
    """Group EventLog rows into time buckets and return sorted DataPoints."""
    counts: dict[tuple[datetime, str], int] = defaultdict(int)
    for event in events:
        key = (_truncate(event.received_at, bucket), event.event_name)
        counts[key] += 1
    return [
        DataPoint(time_bucket=ts, event_name=name, count=count)
        for (ts, name), count in sorted(counts.items())
    ]


@router.post("/", response_model=EmitResponse)
def emit_event(
    payload: EmitRequest,
    publisher: pubsub_v1.PublisherClient = Depends(get_publisher),  # noqa: B008
) -> EmitResponse:
    """Publish an event to the Pub/Sub topic.

    The pulseboard-consumer will pick up the message, write it to event_log,
    and ack it. Returns the Pub/Sub message ID.
    """
    try:
        message_id = publish_event(
            event_name=payload.event_name,
            metadata=payload.metadata,
            publisher=publisher,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {exc}") from exc
    return EmitResponse(published=True, message_id=message_id)


@router.get("/", response_model=EventDataResponse)
def get_events(
    event_name: str | None = None,
    since: datetime | None = None,
    bucket: str = "minute",
    db: Session = Depends(get_db),  # noqa: B008
) -> EventDataResponse:
    """Return time-bucketed event counts from event_log.

    Query params:
      event_name  Filter to a single event type (optional)
      since       ISO timestamp — only return events after this time (default: 1h ago)
      bucket      Time bucket size: "minute" (default) or "hour"
    """
    if bucket not in _VALID_BUCKETS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid bucket '{bucket}'. Must be one of: {sorted(_VALID_BUCKETS)}",
        )

    if since is None:
        since = datetime.now(UTC) - timedelta(hours=1)

    query = db.query(EventLog).filter(EventLog.received_at >= since)
    if event_name:
        query = query.filter(EventLog.event_name == event_name)

    events = query.order_by(EventLog.received_at).all()
    data = _bucket_events(events, bucket)

    return EventDataResponse(event_name=event_name, since=since, bucket=bucket, data=data)
